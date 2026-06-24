#!/usr/bin/env python3
"""
storyworlds/worlds/vision_twist_dialogue_bad_ending_comedy.py
==============================================================

A small storyworld about vision, a twist, dialogue, and a comedy-leaning
bad ending.

Premise:
A child wants to see something important very clearly.
Tension:
The view is blocked by ordinary, silly problems like smudges, glare, and bad
timing.
Twist:
The "mystery" turns out to be something unexpected and funny.
Ending:
The child still does not get the hoped-for result, but the ending image is
clear and comic.

This world is intentionally compact and state-driven rather than a frozen
template. The prose is generated from a tiny world model with physical meters
and emotional memes, plus an ASP twin for the reasonableness gate.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class Setting:
    place: str
    indoors: bool
    affords: set[str] = field(default_factory=set)
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


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    weather: str
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


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    risk_meter: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
    plural: bool = False
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
class Gear:
    id: str
    label: str
    fix_for: str
    prep: str
    tail: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SETTINGS = {
    "window": Setting(place="the window", indoors=True, affords={"peek", "spot", "watch"}),
    "yard": Setting(place="the backyard", indoors=False, affords={"peek", "spot", "watch"}),
    "porch": Setting(place="the porch", indoors=False, affords={"peek", "spot", "watch"}),
}

ACTIVITIES = {
    "peek_parade": Activity(
        id="peek_parade",
        verb="peek at the parade",
        gerund="peeking at the parade",
        rush="run to the window",
        risk="glare",
        weather="sunny",
        keyword="vision",
        tags={"vision", "glare", "crowd"},
    ),
    "spot_bird": Activity(
        id="spot_bird",
        verb="spot the bird",
        gerund="spotting the bird",
        rush="grab the binoculars",
        risk="smudge",
        weather="sunny",
        keyword="vision",
        tags={"vision", "bird", "smudge"},
    ),
    "watch_stars": Activity(
        id="watch_stars",
        verb="watch the stars",
        gerund="watching the stars",
        rush="carry the telescope outside",
        risk="fog",
        weather="foggy",
        keyword="vision",
        tags={"vision", "stars", "fog"},
    ),
}

PRIZES = {
    "glasses": Prize(
        label="glasses",
        phrase="a pair of shiny new glasses",
        type="glasses",
        risk_meter="smudge",
        plural=True,
    ),
    "binoculars": Prize(
        label="binoculars",
        phrase="small green binoculars",
        type="binoculars",
        risk_meter="smudge",
        plural=True,
    ),
    "telescope": Prize(
        label="telescope",
        phrase="a little brass telescope",
        type="telescope",
        risk_meter="fog",
    ),
}

GEAR = [
    Gear(id="cloth", label="a soft cleaning cloth", fix_for="smudge",
         prep="wipe the lenses first", tail="used the cloth and sighed"),
    Gear(id="shade", label="a paper hat brim", fix_for="glare",
         prep="shade the window with a paper hat brim", tail="stood under the brim"),
]


GIRL_NAMES = ["Mia", "Luna", "Nora", "Poppy", "Ivy", "Zoe"]
BOY_NAMES = ["Leo", "Finn", "Max", "Noah", "Theo", "Sam"]
TRAITS = ["curious", "cheerful", "silly", "bouncy", "lively"]


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES["peek_parade" if act_id == "peek" else "spot_bird" if act_id == "spot" else "watch_stars"]
            for prize_id, prize in PRIZES.items():
                if prize.label == "glasses" and act.id == "watch_stars":
                    continue
                if act.risk == prize.risk_meter:
                    combos.append((place, act.id, prize_id))
    return combos


def pick_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if gear.fix_for == activity.risk and prize.risk_meter == activity.risk:
            return gear
    return None


def reasonableness_gate(activity: Activity, prize: Prize) -> bool:
    return activity.risk == prize.risk_meter and pick_gear(activity, prize) is not None


ASP_RULES = r"""
risk_match(A,P) :- act(A,R), prize_risk(P,R).
fixable(A,P) :- risk_match(A,P), gear(G), fixes(G,R), act(A,R).
valid(Place,A,P) :- affords(Place,A), risk_match(A,P), fixable(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, s in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        if s.indoors:
            lines.append(asp.fact("indoors", place))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", place, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("act", aid, a.risk))
        lines.append(asp.fact("activity", aid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_risk", pid, p.risk_meter))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        lines.append(asp.fact("fixes", g.id, g.fix_for))
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
    if py == cl:
        print(f"OK: clingo matches python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy-leaning vision storyworld with a twist and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = rng.choice(list(combos))
    p = _safe_lookup(PRIZES, prize)
    gender = getattr(args, "gender", None) or rng.choice(sorted(p.genders))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def _do_activity(world: World, actor: Entity, activity: Activity, prize: Entity, narrate: bool = True) -> None:
    actor.meters[activity.risk] = actor.meters.get(activity.risk, 0) + 1
    actor.memes["hope"] = actor.memes.get("hope", 0) + 1
    if prize.worn_by == actor.id:
        prize.meters[prize.risk_meter] = prize.meters.get(prize.risk_meter, 0) + 1
        prize.meters["awkward"] = prize.meters.get("awkward", 0) + 1
    if narrate:
        world.say(f"{actor.id} did not want to waste a minute, so {actor.pronoun()} tried to {activity.verb}.")


def predict(world: World, actor: Entity, activity: Activity, prize: Entity) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, sim.get(prize.id), narrate=False)
    prize2 = sim.get(prize.id)
    return {"ruined": prize2.meters.get(prize.risk_meter, 0) >= THRESHOLD}


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=parent_type))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id))
    prize.worn_by = hero.id

    world.say(f"{hero.id} was a {trait} little {hero.type} who cared a lot about {hero.pronoun('possessive')} vision.")
    world.say(f"{hero.id} loved {activity.gerund}, and {hero.pronoun('possessive')} {prize.label} helped {hero.pronoun('object')} see better.")
    world.say(f"That morning, {hero.pronoun('possessive')} {parent.label or parent.type} bought {hero.pronoun('object')} {prize.phrase}.")

    world.para()
    if setting.indoors:
        world.say(f"{hero.id} stood at {setting.place} and squinted at the bright scene outside.")
    else:
        world.say(f"{hero.id} went to {setting.place} with {hero.pronoun('possessive')} {parent.label or parent.type}.")
    world.say(f'"I can see it!" {hero.id} said. "I can, I can!"')

    pred = predict(world, hero, activity, prize)
    if pred["ruined"]:
        world.say(f'"Wait," said {hero.pronoun("possessive")} {parent.label or parent.type}. "If you do that, your {prize.label} will get {activity.risk}."')
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1
        world.say(f"{hero.id} made a dramatic face and tried to {activity.rush}, because children never let a warning finish its sentence.")
        gear = pick_gear(activity, prize_cfg)
        if gear:
            if activity.risk == "glare":
                world.say(f'"How about we {gear.prep}?" said {hero.pronoun("possessive")} {parent.label or parent.type}.')
                hero.memes["conflict"] = hero.memes.get("conflict", 0) + 1
                world.say(f'{hero.id} said, "Fine, but only because the sun was winning."')
            else:
                world.say(f'"Let\'s use {gear.label}," said {hero.pronoun("possessive")} {parent.label or parent.type}.')
        _do_activity(world, hero, activity, prize, narrate=True)

    world.para()
    if activity.id == "watch_stars":
        world.say(f"Then came the twist: the bright speck in the sky was not a star at all.")
        world.say(f'"It is a kite," said {hero.id}. "A tiny fancy kite."')
        world.say(f'"A kite?" said {hero.pronoun("possessive")} {parent.label or parent.type}. "Of course it is. The sky has jokes too."')
        world.say(f"Unfortunately, the clouds slid over the moon right after that, as if the night wanted one more laugh.")
    elif activity.id == "peek_parade":
        world.say(f"Then came the twist: the grand parade was only three bicycles and a dog wearing a ribbon.")
        world.say(f'"That is not a parade," said {hero.id}.')
        world.say(f'"It is now," said {hero.pronoun("possessive")} {parent.label or parent.type}, trying not to laugh.')
        world.say(f"The dog barked once and the whole proud moment rolled away down the street.")
    else:
        world.say(f"Then came the twist: the bird was a painted bird on a sign, blinking in the wind like it knew a secret.")
        world.say(f'"I chased a sign," said {hero.id}.')
        world.say(f'"That happens to the best of us," said {hero.pronoun("possessive")} {parent.label or parent.type}.')
        world.say(f"Then a real bird flew off before anyone could look again.")

    world.para()
    world.say(f"In the end, {hero.id} still did not get the perfect view.")
    world.say(f'{hero.id} sighed, cleaned the {prize.label} with a sleeve, and said, "Well, my vision is a little dramatic today."')
    world.say(f'{hero.pronoun().capitalize()} and {hero.pronoun("possessive")} {parent.label or parent.type} laughed anyway, standing under the dim sky or the bright window like two people who had lost an argument with the universe.')

    world.facts.update(hero=hero, parent=parent, prize=prize, setting=setting, activity=activity, gear=(pick_gear(activity, prize_cfg) if pred["ruined"] else None))
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short comedy story about "vision" where {hero.id} wants to {act.verb} but something silly gets in the way.',
        f'Tell a dialogue-heavy story with a twist: {hero.id} tries to {act.verb}, {hero.pronoun("possessive")} {parent.label or parent.type} warns {hero.pronoun("object")}, and the ending is a funny disappointment.',
        f'Write a child-friendly bad-ending story about {prize.label}, a view problem, and an unexpected reveal.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {act.verb}. {hero.pronoun().capitalize()} cared a lot about {hero.pronoun('possessive')} vision and hoped the {prize.label} would help.",
        ),
        QAItem(
            question=f"Why did {hero.pronoun('possessive')} {parent.label or parent.type} worry?",
            answer=f"{hero.pronoun('possessive').capitalize()} {parent.label or parent.type} worried because the {prize.label} could get {act.risk}, and then seeing would become even harder.",
        ),
        QAItem(
            question="What was the twist?",
            answer="The thing the child was looking at turned out to be something much sillier than it first seemed.",
        ),
        QAItem(
            question="Did the story have a happy ending?",
            answer="No. The ending was funny, but it was still a bad ending because the child did not get the clear view they wanted.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    if "vision" in tags:
        out.append(QAItem("What is vision?", "Vision is the ability to see with your eyes."))
    if "glare" in tags:
        out.append(QAItem("What is glare?", "Glare is very bright light that makes it hard to see clearly."))
    if "smudge" in tags:
        out.append(QAItem("What is a smudge?", "A smudge is a dirty mark that can blur a surface, like a lens or window."))
    if "fog" in tags:
        out.append(QAItem("What is fog?", "Fog is a cloud near the ground that makes the world look hazy."))
    if "crowd" in tags:
        out.append(QAItem("What is a parade?", "A parade is a line of people, vehicles, or performers moving together for a celebration."))
    if "stars" in tags:
        out.append(QAItem("Why can stars be hard to see?", "Stars can be hard to see when clouds, fog, or bright light make the sky less clear."))
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id}: type={e.type} meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="window", activity="peek_parade", prize="glasses", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="yard", activity="spot_bird", prize="binoculars", name="Leo", gender="boy", parent="father", trait="silly"),
    StoryParams(place="porch", activity="watch_stars", prize="telescope", name="Nora", gender="girl", parent="mother", trait="lively"),
]


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(_safe_lookup(PRIZES, prize_id).genders))
    return f"No story: a {_safe_lookup(PRIZES, prize_id).label} is not a typical {gender}'s item here; try {ok}."


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"No story: {activity.verb} and {prize.label} do not make a reasonable risk/fix pair here."


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.parent, params.trait)
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
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
