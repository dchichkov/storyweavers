#!/usr/bin/env python3
"""
storyworlds/worlds/inflict_slope_reflexology_flashback_bedtime_story.py
========================================================================

A small bedtime-story world about a child, a gentle slope, a worried moment,
a flashback, and a soothing reflexology ending.

The source-tale shape is simple:
- A sleepy child and a caring grown-up are on a moonlit slope.
- The child wants to hurry, but that could inflict a little bump or tumble.
- A flashback reminds the child of a previous slip.
- The grown-up chooses reflexology: a calm foot massage and slow breathing.
- The story ends with the child feeling safe, drowsy, and ready for sleep.

This script follows the Storyweavers storyworld contract:
- typed entities with meters and memes
- forward-simulated world state
- a reasonableness gate plus inline ASP twin
- standard CLI, QA, JSON, trace, and verify modes
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    grownup: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "mom"}
        male = {"boy", "father", "grandfather", "man", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    label: str
    slope: bool = False
    nighttime: bool = True
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    consequence: str
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
class Remedy:
    id: str
    label: str
    prep: str
    ending: str
    tags: set[str] = field(default_factory=set)
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
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes.get("worry", 0.0) >= THRESHOLD and ent.memes.get("remember", 0.0) >= THRESHOLD:
            sig = ("calm", ent.id)
            if sig not in world.fired:
                world.fired.add(sig)
                ent.memes["fear"] = max(0.0, ent.memes.get("fear", 0.0) - 1.0)
                ent.memes["trust"] = ent.memes.get("trust", 0.0) + 1.0
                out.append("The old fear got smaller, and the room felt safer.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_risk(world: World, child: Entity, act: Activity) -> bool:
    sim = world.copy()
    sim.get(child.id).meters["tired"] += 1.0
    sim.get(child.id).meters["rush"] += 1.0
    return bool(act.risk == "tumble" and sim.place.slope)


def resolve_recap(world: World, child: Entity) -> None:
    child.memes["remember"] += 1.0
    world.say(
        f"Then {child.id} had a little flashback, remembering the last time {child.pronoun()} tried to hurry on a slope and nearly slipped."
    )


def tell(world: World, child: Entity, grownup: Entity, act: Activity, remedy: Remedy) -> None:
    world.say(
        f"{child.id} was a sleepy little {child.type} who loved the hush of bedtime."
    )
    world.say(
        f"{child.pronoun().capitalize()} wanted to {act.verb}, but {grownup.pronoun('possessive')} gentle voice said the slope could {act.risk} and {act.consequence}."
    )
    child.memes["desire"] = child.memes.get("desire", 0.0) + 1.0
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1.0
    child.meters["tired"] = child.meters.get("tired", 0.0) + 1.0
    world.para()
    resolve_recap(world, child)
    world.say(
        f"{grownup.id} sat beside {child.pronoun('object')} and offered {remedy.label}: {remedy.prep}."
    )
    child.memes["trusted"] = child.memes.get("trusted", 0.0) + 1.0
    _propagate(world, narrate=True)
    world.say(
        f"Slow little circles soothed the feet, and {child.id} learned that going slowly could feel just as nice as hurrying."
    )
    world.say(
        f"At the end of the bedtime story, {child.id} was calm, warm, and ready to sleep while {remedy.ending}."
    )


SETTINGS = {
    "hillside": Place("the moonlit hillside", slope=True, nighttime=True),
    "gardenpath": Place("the quiet garden path", slope=True, nighttime=True),
    "cottage_steps": Place("the cottage steps", slope=True, nighttime=True),
}

ACTIVITIES = {
    "run_down": Activity(
        id="run_down",
        verb="run down the slope",
        gerund="running down the slope",
        rush="dash too quickly",
        risk="tumble",
        consequence="inflict a little bump",
        tags={"slope", "risk"},
    ),
    "skip": Activity(
        id="skip",
        verb="skip along the slope",
        gerund="skipping along the slope",
        rush="take big bouncy steps",
        risk="slip",
        consequence="inflict a sore toe",
        tags={"slope", "risk"},
    ),
    "climb": Activity(
        id="climb",
        verb="climb the slope",
        gerund="climbing the slope",
        rush="hurry uphill",
        risk="stumble",
        consequence="inflict tired feet",
        tags={"slope", "risk"},
    ),
}

REMEDIES = {
    "reflexology": Remedy(
        id="reflexology",
        label="reflexology",
        prep="rub the sleepy feet with warm, careful reflexology circles",
        ending="the lamp glowed softly beside them",
        tags={"reflexology", "care"},
    ),
    "warm_socks": Remedy(
        id="warm_socks",
        label="warm socks",
        prep="pull on a pair of warm socks and let the toes rest",
        ending="the blanket tucked in around the bed",
        tags={"warmth", "care"},
    ),
    "breathing": Remedy(
        id="breathing",
        label="slow breathing",
        prep="count three slow breaths together",
        ending="the pillow waited like a cloud",
        tags={"calm", "care"},
    ),
}

CHILD_NAMES = ["Nia", "Milo", "Luna", "Owen", "Maya", "Ezra", "Tia", "Noel"]
GROWNUP_TYPES = ["mother", "father", "grandmother", "grandfather"]


@dataclass
class StoryParams:
    place: str
    activity: str
    remedy: str
    name: str
    grownup: str
    seed: Optional[int] = None
    samples: list = field(default_factory=list)
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
    combos: list[tuple[str, str, str]] = []
    for place_id, place in SETTINGS.items():
        if not place.slope:
            continue
        for act_id in ACTIVITIES:
            for rem_id in REMEDIES:
                if act_id in {"run_down", "skip", "climb"} and rem_id in {"reflexology", "warm_socks", "breathing"}:
                    combos.append((place_id, act_id, rem_id))
    return combos


def explain_rejection(activity: Activity, remedy: Remedy) -> str:
    return (
        f"(No story: {activity.verb} does not pair with {remedy.label} in a way that makes the bedtime turn feel honest.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world about a slope, a flashback, and reflexology.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
    ap.add_argument("--grownup", choices=GROWNUP_TYPES)
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
    if getattr(args, "activity", None) and getattr(args, "remedy", None):
        act = _safe_lookup(ACTIVITIES, getattr(args, "activity", None))
        rem = _safe_lookup(REMEDIES, getattr(args, "remedy", None))
        if getattr(args, "remedy", None) == "reflexology" and getattr(args, "activity", None) not in {"run_down", "skip", "climb"}:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "remedy", None) is None or c[2] == getattr(args, "remedy", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, remedy = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    grownup = getattr(args, "grownup", None) or rng.choice(GROWNUP_TYPES)
    return StoryParams(place=place, activity=activity, remedy=remedy, name=name, grownup=grownup)


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    child = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in {"Nia", "Luna", "Maya", "Tia"} else "boy"))
    grownup = world.add(Entity(id="Grownup", kind="character", type=params.grownup, label=params.grownup))
    act = _safe_lookup(ACTIVITIES, params.activity)
    rem = _safe_lookup(REMEDIES, params.remedy)

    world.facts.update(child=child, grownup=grownup, act=act, rem=rem)
    tell(world, child, grownup, act, rem)
    story = world.render()
    prompts = [
        f"Write a gentle bedtime story for a small child on a {params.place} that includes a flashback and the word 'reflexology'.",
        f"Tell a soft story where {params.name} wants to {act.verb} but a caring grown-up helps with {rem.label}.",
        f"Write a bedtime story about a slope, a near-slip, and a calm ending.",
    ]
    story_qa = [
        QAItem(
            question=f"Why did {params.name}'s grown-up worry about the slope?",
            answer=f"Because {params.name} wanted to {act.verb}, and that could {act.risk} and {act.consequence}.",
        ),
        QAItem(
            question="What did the flashback remind the child of?",
            answer=f"It reminded {params.name} of an earlier time when hurrying on a slope almost caused a slip.",
        ),
        QAItem(
            question=f"How did {rem.label} help at the end?",
            answer=f"It soothed the sleepy feet and helped {params.name} feel calm enough to rest.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a slope?",
            answer="A slope is a surface that goes up or down instead of staying flat.",
        ),
        QAItem(
            question="What is reflexology?",
            answer="Reflexology is a gentle kind of foot massage that uses careful touch to help someone relax.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly remembers something that happened before the present moment.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={e.meters}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
activity(A) :- act(A).
remedy(R) :- rem(R).

valid(P,A,R) :- place(P), activity(A), remedy(R), slope_place(P), bedtime_style(R).
valid_story(P,A,R) :- valid(P,A,R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if p.slope:
            lines.append(asp.fact("slope_place", pid))
        if p.nighttime:
            lines.append(asp.fact("bedtime_place", pid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("act", aid))
    for rid in REMEDIES:
        lines.append(asp.fact("rem", rid))
        lines.append(asp.fact("bedtime_style", rid))
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
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print("  ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(StoryParams(place=p, activity=a, remedy=r, name="Nia", grownup="mother")) for p, a, r in [
            ("hillside", "run_down", "reflexology"),
            ("gardenpath", "skip", "warm_socks"),
            ("cottage_steps", "climb", "breathing"),
        ]]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            i += 1
            seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if getattr(args, "qa", None):
            print()
            print(build_qa(sample))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
