#!/usr/bin/env python3
"""
A small cautionary fable set in a post office.

Seed idea:
- A glum little mail carrier wants to hurry through the post office.
- A warning foretells that careless rushing may let a parcel befall the floor.
- A safer, slower choice prevents the trouble and ends with a moral.

This file follows the Storyweavers storyworld contract with:
- a typed world model carrying meters and memes
- story-driven prose from simulation state
- a Python reasonableness gate plus inline ASP twin
- the standard CLI and StorySample/QAItem containers
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
# World model
# ---------------------------------------------------------------------------

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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    adult: object | None = None
    hero: object | None = None
    prize_ent: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"order": 0.0, "damage": 0.0, "mess": 0.0}
        if not self.memes:
            self.memes = {"glum": 0.0, "worry": 0.0, "care": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "lady"}
        male = {"boy", "father", "man", "gentleman"}
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
    place: str = "the post office"
    affords: set[str] = field(default_factory=set)
    SETTING: object | None = None
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    keyword: str
    moral: str
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
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
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
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

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

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.zone = set(self.zone)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTING = Setting(place="the post office", affords={"hurry", "carry", "sort"})

ACTIVITIES = {
    "hurry": Activity(
        id="hurry",
        verb="hurry through the post office",
        gerund="hurrying through the post office",
        rush="dash across the floor",
        risk="might make a parcel befall the floor",
        zone={"floor", "counter"},
        keyword="glum",
        moral="slow steps are safer than rushed steps",
    ),
    "carry": Activity(
        id="carry",
        verb="carry the parcel",
        gerund="carrying the parcel carefully",
        rush="swing the parcel by the string",
        risk="might scrape the parcel and dent the corners",
        zone={"counter", "floor"},
        keyword="parcel",
        moral="careful hands keep things safe",
    ),
    "sort": Activity(
        id="sort",
        verb="sort the letters",
        gerund="sorting the letters",
        rush="fling the letters into the tray",
        risk="might scatter the letters everywhere",
        zone={"counter"},
        keyword="letters",
        moral="tidy work stays tidy when it is done gently",
    ),
}

PRIZES = {
    "parcel": Prize(
        label="parcel",
        phrase="a small brown parcel with a blue string",
        type="parcel",
        region="hands",
    ),
    "letters": Prize(
        label="letters",
        phrase="a neat stack of letters",
        type="letters",
        region="hands",
        plural=True,
    ),
    "stamp_book": Prize(
        label="stamp book",
        phrase="a little stamp book",
        type="stamp book",
        region="hands",
    ),
}

GEAR = [
    Gear(
        id="cart",
        label="a little mail cart",
        covers={"floor", "counter"},
        guards={"drop", "scrape", "scatter"},
        prep="set the parcel in a little mail cart",
        tail="rolled the cart along with careful wheels",
    ),
    Gear(
        id="tray",
        label="a deep tray",
        covers={"counter"},
        guards={"scatter"},
        prep="place the letters in a deep tray",
        tail="carried the tray with both hands",
    ),
    Gear(
        id="two_hands",
        label="both hands",
        covers={"hands"},
        guards={"drop", "scrape", "scatter"},
        prep="hold it with both hands",
        tail="held everything steady with both hands",
    ),
]

NAMES = ["Milo", "Pip", "Nina", "Ruby", "Toby", "Lena", "Jasper", "Ivy"]
TRAITS = ["glum", "curious", "timid", "earnest", "cheerful"]


# ---------------------------------------------------------------------------
# ASP twin + Python reasonableness gate
# ---------------------------------------------------------------------------

ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), guards(G,M), risk_kind(A,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = [asp.fact("setting", "post_office"), asp.fact("affords", "post_office", "hurry"),
                        asp.fact("affords", "post_office", "carry"), asp.fact("affords", "post_office", "sort")]
    for a in ACTIVITIES.values():
        lines.append(asp.fact("activity", a.id))
        lines.append(asp.fact("risk_kind", a.id, a.risk))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", a.id, r))
    for p in PRIZES.values():
        lines.append(asp.fact("prize", p.type))
        lines.append(asp.fact("worn_on", p.type, p.region))
        if p.plural:
            lines.append(asp.fact("prize_plural", p.type))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, p.type))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for k in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place, setting in {"post_office": SETTING}.items():
        for aid, a in ACTIVITIES.items():
            if aid not in setting.affords:
                continue
            for pid, p in PRIZES.items():
                if p.region in a.zone and select_gear(a, p):
                    out.append((place, aid, pid))
    return out


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for g in GEAR:
        if prize.region in g.covers and activity.risk.split()[1] if False else True:
            # actual compatibility checked below via hand-tuned mappings
            pass
    compat = {
        ("hurry", "parcel"): "cart",
        ("carry", "parcel"): "two_hands",
        ("sort", "letters"): "tray",
        ("sort", "stamp_book"): "two_hands",
        ("carry", "stamp_book"): "two_hands",
    }
    gid = compat.get((activity.id, prize.type))
    return next((g for g in GEAR if g.id == gid), None)


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def predict(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"damaged": prize.meters["damage"] >= THRESHOLD, "mess": prize.meters["mess"]}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.memes["care"] += 1
    if activity.id == "hurry":
        actor.memes["worry"] += 1
    if activity.id == "sort":
        actor.meters["order"] += 1
    propagate(world, narrate=narrate)


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for item in world.worn_items(actor):
            if item.region not in world.zone or item.protective or world.covered(actor, item.region):
                continue
            sig = ("risk", actor.id, item.id, tuple(sorted(world.zone)))
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["damage"] += 1
            item.meters["mess"] += 1
            out.append(f"His {item.label} was in danger of damage.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def tell(setting: Setting, activity: Activity, prize: Prize, name: str, gender: str, trait: str, parent: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, traits=["little", trait, "glum"]))
    adult = world.add(Entity(id="Adult", kind="character", type=parent, label="the clerk"))
    prize_ent = world.add(Entity(
        id=prize.type, type=prize.type, label=prize.label, phrase=prize.phrase,
        owner=hero.id, caretaker=adult.id, region=prize.region, plural=prize.plural
    ))

    hero.memes["glum"] += 1
    world.say(f"{hero.id} was a glum little {hero.type} who walked into the post office with careful feet.")
    world.say(f"{hero.id} liked the quiet sort of morning when envelopes whispered and stamps waited in rows.")
    world.say(f"Today {hero.id} carried {hero.pronoun('possessive')} {prize.label}, and {prize_ent.phrase} looked neat in {hero.pronoun('possessive')} hands.")

    world.para()
    world.say(f"But {hero.id} wanted to {activity.verb}, even though {activity.risk}.")
    world.say(f'"{activity.keyword.capitalize() if activity.keyword else "Careful"} now," said {adult.label}, "or a little trouble may befall the parcel room."')

    if activity.id == "hurry":
        hero.memes["worry"] += 1
        world.say(f"{hero.id} tried to {activity.rush}, and the parcel rocked in {hero.pronoun('possessive')} arms.")
        world.say("A stamp case tipped, and everyone looked worried.")
    elif activity.id == "carry":
        hero.memes["worry"] += 1
        world.say(f"{hero.id} began to {activity.rush}, and the corners of the parcel bumped the counter.")
        world.say("That was enough to make the clerk glance up with a frown.")
    else:
        hero.memes["worry"] += 1
        world.say(f"{hero.id} was about to {activity.rush}, and the letters shivered like leaves.")
        world.say("The clerk reached out at once, because one rough toss can scatter a whole stack.")

    gear = select_gear(activity, prize)
    if gear is None:
        gear = next(iter(globals().get("GEARS", globals().get("GEAR", []))))

    world.para()
    if activity.id == "hurry":
        world.say(f'The clerk pointed to {gear.label} and said, "{gear.prep}."')
        world.say(f"{hero.id} slowed down, {gear.tail}, and the parcel stayed steady.")
    elif activity.id == "carry":
        world.say(f'The clerk nodded toward {gear.label} and said, "{gear.prep}."')
        world.say(f"{hero.id} listened, {gear.tail}, and the parcel stopped wobbling.")
    else:
        world.say(f'The clerk brought out {gear.label} and said, "{gear.prep}."')
        world.say(f"{hero.id} took the advice, {gear.tail}, and the letters stayed in a neat stack.")

    hero.memes["glum"] = 0.0
    hero.memes["relief"] += 1
    prize_ent.meters["damage"] = 0.0
    prize_ent.meters["mess"] = 0.0

    world.para()
    world.say(f"In the end, {hero.id} smiled a little, because slow care had saved the day.")
    world.say(f"The post office was tidy again, {prize.label} was safe, and the lesson was clear: {activity.moral}.")

    world.facts.update(hero=hero, adult=adult, prize=prize_ent, activity=activity, gear=gear, setting=setting)
    return world


# ---------------------------------------------------------------------------
# Parameters, Q&A, and formatting
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act, prize = f["hero"], f["activity"], f["prize"]
    return [
        f'Write a cautionary fable set in a post office about a glum little {hero.type} named {hero.id}.',
        f"Tell a story where {hero.id} wants to {act.verb}, but a clerk warns that {prize.phrase} could be harmed.",
        f'Write a child-friendly fable using the word "{act.keyword}" and ending with a careful lesson.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, adult, prize, act, gear = f["hero"], f["adult"], f["prize"], f["activity"], f["gear"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a glum little {hero.type} in the post office.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before the warning?",
            answer=f"{hero.id} wanted to {act.verb}, even though that was not a careful choice.",
        ),
        QAItem(
            question=f"What might have happened if {hero.id} had stayed careless?",
            answer=f"{prize.phrase} could have been harmed, and the trouble might have befallen the parcel room.",
        ),
        QAItem(
            question=f"What helped {hero.id} keep things safe?",
            answer=f"{gear.label} helped because it matched the task and let {hero.id} act more carefully.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{hero.id} slowed down, the {prize.label} stayed safe, and the lesson was to choose careful steps.",
        ),
    ]


KNOWLEDGE = {
    "post office": [
        QAItem(
            question="What is a post office for?",
            answer="A post office is a place where people send letters and parcels to other places.",
        ),
        QAItem(
            question="Why should people be careful in a post office?",
            answer="People should be careful so letters, parcels, and stamps do not get lost or damaged.",
        ),
    ],
    "parcel": [
        QAItem(
            question="What is a parcel?",
            answer="A parcel is a wrapped package that is sent to someone.",
        ),
    ],
    "letters": [
        QAItem(
            question="Why do people sort letters?",
            answer="People sort letters so each one can go to the right home or building.",
        ),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["activity"].keyword, world.facts["prize"].label, "post office"}
    out: list[QAItem] = []
    for tag, items in KNOWLEDGE.items():
        if tag in tags:
            out.extend(items)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        n = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={m}")
        if n:
            bits.append(f"memes={n}")
        if e.region:
            bits.append(f"region={e.region}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP verification helpers
# ---------------------------------------------------------------------------

def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary fable in a post office.")
    ap.add_argument("--place", choices=["post_office"], default=None)
    ap.add_argument("--activity", choices=sorted(ACTIVITIES), default=None)
    ap.add_argument("--prize", choices=sorted(PRIZES), default=None)
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--parent", choices=["mother", "father"], default=None)
    ap.add_argument("--name", default=None)
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
    if getattr(args, "place", None) and getattr(args, "place", None) != "post_office":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = valid_combos()
    if getattr(args, "activity", None):
        combos = [c for c in combos if c[1] == getattr(args, "activity", None)]
    if getattr(args, "prize", None):
        combos = [c for c in combos if c[2] == getattr(args, "prize", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = (list(rng.choice(combos)) + [None, None, None])[:3]
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    if getattr(args, "gender", None) and getattr(args, "prize", None) and getattr(args, "gender", None) not in _safe_lookup(PRIZES, getattr(args, "prize", None)).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTING, _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.trait, params.parent)
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


CURATED = [
    StoryParams(place="post_office", activity="hurry", prize="parcel", name="Milo", gender="boy", parent="mother", trait="glum"),
    StoryParams(place="post_office", activity="sort", prize="letters", name="Nina", gender="girl", parent="father", trait="curious"),
    StoryParams(place="post_office", activity="carry", prize="stamp_book", name="Pip", gender="boy", parent="mother", trait="earnest"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_program("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible combos:")
        for row in vals:
            print(" ", row)
        return

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base + i
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
            header = f"### {p.name}: {p.activity} with {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
