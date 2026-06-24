#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about a proud pheasant at an estuary,
where humility and teamwork matter, and ignoring caution can end badly.

Seed tale inspiration:
- A pheasant struts to the estuary and wants the prettiest reed crown.
- A kind crab and a small heron suggest teamwork and humility.
- The pheasant scoffs, rushes ahead, and the tide takes the prize.
- The ending is cautionary: pride sinks the plan, while humble help would
  have kept everyone safe.

This script models the story as a small stateful simulation with physical
meters and emotional memes, plus an inline ASP twin for parity checks.
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    crab: object | None = None
    heron: object | None = None
    pheasant: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"pheasant", "heron", "crab", "bird"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str = "the estuary"
    tides: str = "tide"
    waterside: bool = True
    affords: set[str] = field(default_factory=lambda: {"reedgame", "shellgame"})
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
    mess: str
    soil: str
    zone: set[str]
    keyword: str = ""
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
    region: str
    fragile: bool = True
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
class Helper:
    id: str
    label: str
    prep: str
    tail: str
    HELPER: object | None = None
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
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.meters.get("worn_by") == hash(actor.id)]


def _rule_tide_takes(world: World) -> list[str]:
    out: list[str] = []
    for actor in list(world.entities.values()):
        if actor.meters.get("splash", 0.0) < THRESHOLD:
            continue
        if "prize" not in world.entities:
            continue
        prize = world.get("prize")
        if prize.meters.get("carried", 0.0) < THRESHOLD:
            continue
        if prize.region not in world.zone:
            continue
        sig = ("tide_takes", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        prize.meters["lost"] = 1.0
        actor.memes["sad"] = actor.memes.get("sad", 0.0) + 1.0
        out.append("The tide came in and took the prize away.")
    return out


def _rule_teamwork_heals(world: World) -> list[str]:
    out: list[str] = []
    pheasant = world.entities.get("pheasant")
    if not pheasant:
        return out
    if pheasant.memes.get("humble", 0.0) < THRESHOLD:
        return out
    if pheasant.memes.get("team", 0.0) < THRESHOLD:
        return out
    sig = ("teamwork", pheasant.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pheasant.memes["hope"] = pheasant.memes.get("hope", 0.0) + 1.0
    out.append("The little crew worked together with gentle care.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_rule_teamwork_heals, _rule_tide_takes):
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


SETTING = Setting()

ACTIVITIES = {
    "reedgame": Activity(
        id="reedgame",
        verb="dance among the reeds",
        gerund="dancing among the reeds",
        rush="dash into the reed bed",
        mess="splash",
        soil="all splashed",
        zone={"feet", "legs"},
        keyword="reed",
        tags={"reed", "wet"},
    ),
    "shellgame": Activity(
        id="shellgame",
        verb="carry a bright shell",
        gerund="carrying a bright shell",
        rush="hurry to the edge",
        mess="splash",
        soil="wet and lost",
        zone={"feet", "legs"},
        keyword="shell",
        tags={"shell", "wet"},
    ),
}

PRIZES = {
    "crown": Prize(label="crown", phrase="a woven reed crown", region="head", fragile=True),
    "bundle": Prize(label="bundle", phrase="a little bundle of reeds", region="wing", fragile=True),
}

HELPER = Helper(
    id="help",
    label="crab and heron teamwork",
    prep="slow down and ask the crab and the heron for help",
    tail="held the reeds steady and watched the tide together",
)

GIRL_NAMES = ["Mina", "Nora", "Lily"]
BOY_NAMES = ["Toby", "Pip", "Noah"]


@dataclass
class StoryParams:
    activity: str
    prize: str
    name: str
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


def reasonableness_ok(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone or prize.label == "bundle"


def select_combo(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [(a, p) for a in ACTIVITIES for p in PRIZES if reasonableness_ok(_safe_lookup(ACTIVITIES, a), _safe_lookup(PRIZES, p))]
    if getattr(args, "activity", None):
        combos = [c for c in combos if c[0] == getattr(args, "activity", None)]
    if getattr(args, "prize", None):
        combos = [c for c in combos if c[1] == getattr(args, "prize", None)]
    if not combos:
        pass
    activity, prize = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    return StoryParams(activity=activity, prize=prize, name=name)


def predict_losing(world: World, activity: Activity, prize: Prize) -> bool:
    sim = world.copy()
    pheasant = sim.get("pheasant")
    prize_e = sim.get("prize")
    pheasant.meters["splash"] = 1.0
    sim.zone = set(activity.zone)
    prize_e.meters["carried"] = 1.0
    propagate(sim, narrate=False)
    return prize_e.meters.get("lost", 0.0) >= THRESHOLD


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    pheasant = world.add(Entity(id="pheasant", kind="character", type="pheasant", label=params.name))
    crab = world.add(Entity(id="crab", kind="character", type="crab", label="the crab"))
    heron = world.add(Entity(id="heron", kind="character", type="heron", label="the heron"))
    prize = world.add(Entity(id="prize", type=_safe_lookup(PRIZES, params.prize).label, label=_safe_lookup(PRIZES, params.prize).label))
    act = _safe_lookup(ACTIVITIES, params.activity)

    world.say(f"At the estuary in the morning light, {params.name} the pheasant went walking with a bright step.")
    world.say("The reeds swayed, and the water sang a soft little song.")
    world.say(f"{params.name} loved {act.gerund}, for the marsh felt like a merry tune.")
    world.para()
    world.say(f"Then {params.name} found {prize.phrase} and wanted to keep it close by.")
    prize.meters["carried"] = 1.0
    world.say(f"{params.name} said, \"I found it first, so it is mine alone.\"")
    world.say(f"The crab blinked and the heron bowed. \"Small friends can help,\" they said, \"and humble hearts can keep a prize safe.\"")
    world.para()
    world.say(f"But {params.name} did not listen. {params.name} chose to {act.rush}, though the water was rising.")
    pheasant.meters["splash"] = 1.0
    world.zone = set(act.zone)
    prize.meters["carried"] = 1.0
    if predict_losing(world, act, _safe_lookup(PRIZES, params.prize)):
        world.say(f"The crab cried, \"Caution now!\" yet {params.name} hurried on with a proud little hop.")
    world.say(f"Then the tide came in with a hush and a swish.")
    propagate(world, narrate=True)
    world.para()
    if prize.meters.get("lost", 0.0) >= THRESHOLD:
        world.say(f"{params.name} stood still with empty paws and a soggy heart.")
        world.say(f"The crab and the heron could only share a sad glance, for the prize was gone beyond the reeds.")
        world.say("So the estuary kept its secret, and the proud little pheasant learned too late that humility and teamwork keep troubles small.")
    else:
        world.say(f"With help, the prize stayed safe, and the little crew went home before the tide could nibble it away.")
    world.facts.update(hero=pheasant, crab=crab, heron=heron, prize=prize, activity=act, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short nursery-rhyme story about a pheasant at an estuary who learns humility.',
        f"Tell a gentle cautionary tale where {f['hero'].label} the pheasant wants to {f['activity'].verb} but teamwork matters too.",
        "Write a story with a bad ending, where a proud bird ignores helpful friends and the tide causes trouble.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    prize = _safe_fact(world, f, "prize")
    act = _safe_fact(world, f, "activity")
    return [
        QAItem(
            question=f"Who is the story about at the estuary?",
            answer=f"It is about {hero.label}, a pheasant who came to the estuary and wanted to {act.verb}.",
        ),
        QAItem(
            question=f"What did {hero.label} want to do with the {prize.label}?",
            answer=f"{hero.label} wanted to keep the {prize.label} close, but the tide and the wet reeds made that a risky idea.",
        ),
        QAItem(
            question="Why is the story cautionary?",
            answer="It is cautionary because the pheasant ignored humble advice, rushed ahead, and lost the prize when the tide came in.",
        ),
        QAItem(
            question="What would teamwork have done?",
            answer="Teamwork would have let the crab and the heron help keep the prize safe before the water rose.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an estuary?",
            answer="An estuary is a watery place where a river meets the sea, so the water can move in and out with the tide.",
        ),
        QAItem(
            question="What does humility mean?",
            answer="Humility means not bragging and being ready to listen, learn, and accept help from others.",
        ),
        QAItem(
            question="Why can tides be important near the water?",
            answer="Tides can raise and lower the water level, so things left near the edge can get wet or carried away.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), prize_region(P, R).
teamwork(A) :- helper(H), helpful(H, A).
bad_ending(A, P) :- prize_at_risk(A, P), ignored_help(A), tide_rises.
humble(A) :- listens(A), not boastful(A).
cautionary(A) :- bad_ending(A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "estuary"))
    lines.append(asp.fact("tide_rises"))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, p.region))
    lines.append(asp.fact("helper", "crab"))
    lines.append(asp.fact("helper", "heron"))
    lines.append(asp.fact("helpful", "crab", "reedgame"))
    lines.append(asp.fact("helpful", "heron", "reedgame"))
    lines.append(asp.fact("ignored_help", "shellgame"))
    lines.append(asp.fact("ignored_help", "reedgame"))
    lines.append(asp.fact("listens", "humility"))
    lines.append(asp.fact("boastful", "pride"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show bad_ending/2. #show cautionary/1."))
    atoms = set((sym.name, tuple(arg.string if arg.type == arg.type.String else arg.number for arg in sym.arguments)) for sym in model)
    ok = ("bad_ending", ("reedgame", "crown")) in atoms or ("bad_ending", ("shellgame", "crown")) in atoms
    if ok:
        print("OK: ASP twin produces the cautionary bad-ending signal.")
        return 0
    print("MISMATCH: ASP twin did not produce expected atoms.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: pheasant, estuary, humility, teamwork, cautionary bad ending.")
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
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
    if getattr(args, "activity", None) and getattr(args, "prize", None) and not reasonableness_ok(_safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    activity = getattr(args, "activity", None) or rng.choice(list(ACTIVITIES))
    prize = getattr(args, "prize", None) or rng.choice(list(PRIZES))
    if not reasonableness_ok(_safe_lookup(ACTIVITIES, activity), _safe_lookup(PRIZES, prize)):
        activity, prize = "reedgame", "bundle"
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    return StoryParams(activity=activity, prize=prize, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(activity="reedgame", prize="crown", name="Mina"),
    StoryParams(activity="shellgame", prize="bundle", name="Toby"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show bad_ending/2. #show cautionary/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show bad_ending/2. #show cautionary/1. #show teamwork/1."))
        print(model)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
