#!/usr/bin/env python3
"""
storyworlds/worlds/figure_conflict_lesson_learned_adventure.py
==============================================================

A small adventure storyworld built around a cherished figure, a conflict over
carelessness, and a lesson learned through a safer plan.

The domain is intentionally tiny:
- a child and a guide go on an adventure,
- the child carries a figure they care about,
- the adventure creates a clear risk,
- the guide proposes a reasonable fix,
- the child learns a lesson and the ending shows the change.

This file is standalone and follows the Storyweavers storyworld contract.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    figure: object | None = None
    helper: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dusty": 0.0, "wet": 0.0, "broken": 0.0, "lost": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "fear": 0.0, "conflict": 0.0, "lesson": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    tag: str
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
class Challenge:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    tag: str
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
class FigureItem:
    label: str
    phrase: str
    region: str
    fragile: bool = True
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
    phrase: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
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
        self.zone: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

    def covered(self, actor: Entity, region: str) -> bool:
        return any(item.protective and region in item.covers for item in self.worn_items(actor))

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
        clone.paragraphs = [[]]
        return clone


def _apply_wet(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wet"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("wet", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] += 1
            item.meters["broken"] += 1
            out.append(f"{actor.id}'s {item.label} got wet and bent out of shape.")
    return out


def _apply_loss(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["broken"] < THRESHOLD and item.meters["wet"] < THRESHOLD:
            continue
        if not item.caretaker:
            continue
        sig = ("loss", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["conflict"] += 1
        out.append(f"That would make {carer.id} worry more about the day.")
    return out


RULES = [_apply_wet, _apply_loss]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def challenge_at_risk(challenge: Challenge, figure: FigureItem) -> bool:
    return figure.region in challenge.zone


def select_gear(challenge: Challenge, figure: FigureItem) -> Optional[Gear]:
    for gear in GEAR:
        if challenge.risk in gear.guards and figure.region in gear.covers:
            return gear
    return None


def predict(world: World, hero: Entity, challenge: Challenge, figure_id: str) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters["wet"] += 1
    sim.zone = set(challenge.zone)
    propagate(sim, narrate=False)
    fig = sim.get(figure_id)
    return {"ruined": fig.meters["broken"] >= THRESHOLD}


SETTING = Setting(place="the river trail", tag="trail", affords={"cross_stream", "climb_hill", "enter_cave"})
CHALLENGES = {
    "cross_stream": Challenge(
        id="cross_stream",
        verb="cross the stream",
        gerund="crossing the stream",
        rush="dash across the rocks",
        risk="wet",
        zone={"hands", "feet"},
        tag="water",
    ),
    "climb_hill": Challenge(
        id="climb_hill",
        verb="climb the hill",
        gerund="climbing the hill",
        rush="scramble up the steep slope",
        risk="dusty",
        zone={"hands", "feet"},
        tag="height",
    ),
    "enter_cave": Challenge(
        id="enter_cave",
        verb="explore the cave",
        gerund="exploring the cave",
        rush="duck into the dark cave",
        risk="wet",
        zone={"hands", "torso"},
        tag="dark",
    ),
}

FIGURES = {
    "wooden_figure": FigureItem(
        label="wooden figure",
        phrase="a small carved wooden figure",
        region="hands",
        fragile=True,
    ),
    "paper_figure": FigureItem(
        label="paper figure",
        phrase="a folded paper figure",
        region="hands",
        fragile=True,
    ),
    "glass_figure": FigureItem(
        label="glass figure",
        phrase="a tiny glass figure",
        region="hands",
        fragile=True,
    ),
}

GEAR = [
    Gear(
        id="pouch",
        label="a cloth pouch",
        phrase="a cloth pouch with a string tie",
        covers={"hands"},
        guards={"wet", "dusty"},
        prep="put the figure in a cloth pouch first",
        tail="kept the pouch tied shut",
    ),
    Gear(
        id="wrap",
        label="a wrapped bundle",
        phrase="a soft wrap for carrying delicate things",
        covers={"hands", "torso"},
        guards={"wet"},
        prep="wrap the figure in a soft cloth first",
        tail="carried the bundle carefully",
    ),
    Gear(
        id="satchel",
        label="a small satchel",
        phrase="a small satchel with a flap",
        covers={"hands"},
        guards={"wet", "dusty"},
        prep="slip the figure into a small satchel first",
        tail="buckled the satchel closed",
    ),
]

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Zoe", "Iris"]
BOY_NAMES = ["Theo", "Eli", "Finn", "Max", "Noah", "Leo"]
TRAITS = ["brave", "curious", "cheerful", "careful", "spunky"]


@dataclass
class StoryParams:
    place: str
    challenge: str
    figure: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in {"trail": SETTING}.items():
        for ch_id in setting.affords:
            ch = _safe_lookup(CHALLENGES, ch_id)
            for fig_id, fig in FIGURES.items():
                if challenge_at_risk(ch, fig) and select_gear(ch, fig):
                    combos.append((place, ch_id, fig_id))
    return combos


def reason_invalid(challenge: Challenge, figure: FigureItem) -> str:
    if not challenge_at_risk(challenge, figure):
        return f"(No story: {challenge.gerund} does not threaten a {figure.label} here.)"
    return f"(No story: there is no safe gear for a {figure.label} on this challenge.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "challenge", None) and getattr(args, "figure", None):
        ch, fig = _safe_lookup(CHALLENGES, getattr(args, "challenge", None)), _safe_lookup(FIGURES, getattr(args, "figure", None))
        if not (challenge_at_risk(ch, fig) and select_gear(ch, fig)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "challenge", None) is None or c[1] == getattr(args, "challenge", None))
              and (getattr(args, "figure", None) is None or c[2] == getattr(args, "figure", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, challenge, figure = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or ("mother" if gender == "girl" else "father")
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, challenge=challenge, figure=figure, name=name, gender=gender, helper=helper, trait=trait)


def _do_challenge(world: World, hero: Entity, challenge: Challenge, narrate: bool = True) -> None:
    world.zone = set(challenge.zone)
    hero.meters["wet"] += 1
    hero.memes["joy"] += 1
    propagate(world, narrate=narrate)


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper, label=f"the {params.helper}"))
    figure = world.add(Entity(
        id="figure",
        type="thing",
        label=_safe_lookup(FIGURES, params.figure).label,
        phrase=_safe_lookup(FIGURES, params.figure).phrase,
        owner=hero.id,
        caretaker=helper.id,
        region=_safe_lookup(FIGURES, params.figure).region,
    ))

    ch = _safe_lookup(CHALLENGES, params.challenge)

    world.say(f"{hero.id} was a {params.trait} little {params.gender} who loved adventure.")
    world.say(f"{hero.id} carried {figure.phrase} everywhere, because the little figure felt like a lucky friend.")
    world.para()
    world.say(f"One day, {hero.id} and {helper.label} went to {SETTING.place} to {ch.verb}.")
    world.say(f"{hero.id} wanted to hurry, because the path looked exciting and the stream sparkled ahead.")
    predicted = predict(world, hero, ch, figure.id)
    if predicted["ruined"]:
        world.say(f'"If you rush now, your {figure.label} could get hurt," {helper.label} warned.')
    world.para()

    hero.memes["conflict"] += 1
    world.say(f"{hero.id} frowned and tried to {ch.rush}, even though the warning made {hero.id} uneasy.")
    if predicted["ruined"]:
        world.say(f"{hero.id} almost learned the hard way when the rocks looked slippery and the water splashed high.")
    gear = select_gear(ch, _safe_lookup(FIGURES, params.figure))
    if gear is None:
        gear = next(iter(globals().get("GEARS", globals().get("GEAR", []))))
    protective = world.add(Entity(
        id=gear.id,
        type="thing",
        label=gear.label,
        phrase=gear.phrase,
        owner=hero.id,
        caretaker=helper.id,
        protective=True,
        covers=set(gear.covers),
    ))
    protective.worn_by = hero.id

    world.say(f"Then {helper.label} had a better idea: {gear.prep}.")
    world.say(f"{hero.id} nodded, because {hero.id} could see the plan was safer.")
    hero.memes["conflict"] = 0.0
    hero.memes["lesson"] += 1
    world.say(f"{hero.id} learned that brave adventure does not mean careless feet.")
    world.para()

    _do_challenge(world, hero, ch)
    world.say(
        f"In the end, {hero.id} {ch.gerund}, {gear.tail}, and the {figure.label} stayed safe and dry."
    )
    world.say(
        f"{hero.id} smiled at the tiny figure on the trail, knowing the best adventure was the one that came home whole."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        figure=figure,
        gear=gear,
        challenge=ch,
        setting=SETTING,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, ch, figure = f["hero"], f["helper"], f["challenge"], f["figure"]
    return [
        f'Write a short adventure story for a young child about {hero.id}, a {figure.label}, and a safe choice.',
        f'Tell a gentle adventure where {hero.id} wants to {ch.verb} but {helper.label} worries about the {figure.label}.',
        f'Write a story that includes a conflict, a lesson learned, and a little figure kept safe on an adventure trail.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, fig, ch = f["hero"], f["helper"], f["figure"], f["challenge"]
    qa = [
        QAItem(
            question=f"What did {hero.id} carry on the adventure?",
            answer=f"{hero.id} carried {fig.phrase} on the adventure.",
        ),
        QAItem(
            question=f"Why did {helper.label} warn {hero.id} before they tried to {ch.verb}?",
            answer=f"{helper.label} warned {hero.id} because rushing could have hurt the {fig.label}.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn by the end?",
            answer=f"{hero.id} learned that brave adventure should also be careful and safe.",
        ),
        QAItem(
            question=f"How did the story end for the {fig.label}?",
            answer=f"The {fig.label} stayed safe and dry because {hero.id} used the protective gear first.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a figure?",
            answer="A figure is a small shaped object or model, like a little carved toy or statue.",
        ),
        QAItem(
            question="What does it mean to be careful on a trail?",
            answer="Being careful on a trail means watching your steps, listening for warnings, and avoiding danger.",
        ),
        QAItem(
            question="Why use a pouch or satchel for something delicate?",
            answer="A pouch or satchel helps protect something delicate from bumps, dirt, and water.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
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
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(C,F) :- challenge(C), figure(F), challenge_zone(C,R), figure_region(F,R).
safe_gear(G,C,F) :- gear(G), prize_at_risk(C,F), challenge_risk(C,M), gear_guards(G,M), gear_covers(G,R), figure_region(F,R).
valid_story(P,C,F) :- setting(P), affords(P,C), prize_at_risk(C,F), safe_gear(_,C,F).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "trail"))
    for c in sorted(SETTING.affords):
        lines.append(asp.fact("affords", "trail", c))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("challenge_risk", cid, c.risk))
        for r in sorted(c.zone):
            lines.append(asp.fact("challenge_zone", cid, r))
    for fid, f in FIGURES.items():
        lines.append(asp.fact("figure", fid))
        lines.append(asp.fact("figure_region", fid, f.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("gear_guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("gear_covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small adventure storyworld about a figure, conflict, and a lesson learned.")
    ap.add_argument("--place", choices=["trail"])
    ap.add_argument("--challenge", choices=sorted(CHALLENGES))
    ap.add_argument("--figure", choices=sorted(FIGURES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father"])
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


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} valid story combos:")
        for t in triples:
            print("  ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams("trail", "cross_stream", "wooden_figure", "Mina", "girl", "mother", "brave"),
            StoryParams("trail", "climb_hill", "paper_figure", "Theo", "boy", "father", "curious"),
            StoryParams("trail", "enter_cave", "glass_figure", "Ava", "girl", "mother", "careful"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
