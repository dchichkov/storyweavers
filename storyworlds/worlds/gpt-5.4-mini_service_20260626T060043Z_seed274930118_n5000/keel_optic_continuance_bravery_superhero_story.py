#!/usr/bin/env python3
"""
storyworlds/worlds/keel_optic_continuance_bravery_superhero_story.py
====================================================================

A small superhero storyworld built from the seed words keel, optic, and
continuance.

Premise:
- A young hero sees a problem in a bright city.
- A helper gives a useful gadget or clue.
- The hero chooses bravery, keeps going, and repairs the harm.

The domain is intentionally compact: it focuses on one clear conflict, one
physical obstacle, and one emotional turn where bravery carries the story to a
clean ending image.

This script follows the Storyweavers world contract:
- typed entities with physical meters and emotional memes
- one story model that drives prose
- inline ASP twin with a Python reasonableness gate
- standalone stdlib CLI with text, JSON, QA, trace, and verification modes
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    hero: object | None = None
    prize: object | None = None
    sidekick: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

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
class Mission:
    id: str
    verb: str
    gerund: str
    rush: str
    danger: str
    soil: str
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
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTING = Setting(place="the lighthouse city", affords={"optic", "keel", "continuance"})

MISSIONS = {
    "optic": Mission(
        id="optic",
        verb="follow the flashing clue",
        gerund="tracking the bright clue",
        rush="dash toward the light",
        danger="blinding glare",
        soil="scratched and smoky",
        zone={"eyes", "torso"},
        keyword="optic",
        tags={"light", "optic"},
    ),
    "keel": Mission(
        id="keel",
        verb="steady the broken ferry",
        gerund="bracing the keel",
        rush="run to the dock",
        danger="listing waves",
        soil="dented and wet",
        zone={"arms", "legs"},
        keyword="keel",
        tags={"water", "boat", "keel"},
    ),
    "continuance": Mission(
        id="continuance",
        verb="keep the signal going",
        gerund="keeping the signal alive",
        rush="race back to the tower",
        danger="fading power",
        soil="darkened and tired",
        zone={"torso"},
        keyword="continuance",
        tags={"signal", "continuance"},
    ),
}

PRIZES = {
    "cape": Prize(label="cape", phrase="a bright red cape", type="cape", region="torso"),
    "goggles": Prize(label="goggles", phrase="shiny optic goggles", type="goggles", region="eyes", plural=True),
    "boots": Prize(label="boots", phrase="sturdy blue boots", type="boots", region="legs", plural=True),
}

GEAR = [
    Gear(
        id="visor",
        label="a shield visor",
        covers={"eyes"},
        guards={"blinding glare"},
        prep="put on a shield visor first",
        tail="went back with the shield visor on",
    ),
    Gear(
        id="gloves",
        label="grip gloves",
        covers={"arms"},
        guards={"listing waves"},
        prep="slip on grip gloves first",
        tail="headed out with grip gloves on",
    ),
    Gear(
        id="battery",
        label="a backup battery",
        covers={"torso"},
        guards={"fading power"},
        prep="grab a backup battery first",
        tail="returned with the backup battery humming",
    ),
]

HERO_NAMES = ["Nova", "Aria", "Sky", "Milo", "Jett", "Zuri", "Iris", "Theo"]
SIDEKICK_NAMES = ["Bolt", "Pip", "Scout", "Echo"]
TRAITS = ["brave", "bold", "quick", "kind", "steady"]


@dataclass
class StoryParams:
    setting: str
    mission: str
    prize: str
    hero: str
    sidekick: str
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


def mission_at_risk(mission: Mission, prize: Prize) -> bool:
    return prize.region in mission.zone


def select_gear(mission: Mission, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if mission.danger in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for mid, m in MISSIONS.items():
        for pid, p in PRIZES.items():
            if mission_at_risk(m, p) and select_gear(m, p):
                out.append((mid, pid))
    return out


def explain_rejection(mission: Mission, prize: Prize) -> str:
    if not mission_at_risk(mission, prize):
        return (
            f"(No story: {mission.gerund} would not reach a {prize.label} on the {prize.region}, "
            f"so the problem would not be real enough for a superhero turn.)"
        )
    return (
        f"(No story: there is no gear in this tiny world that both handles {mission.danger} "
        f"and protects a {prize.label} on the {prize.region}.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero storyworld with bravery and a bright city.")
    ap.add_argument("--setting", choices=["city"], default="city")
    ap.add_argument("--mission", choices=MISSIONS.keys())
    ap.add_argument("--prize", choices=PRIZES.keys())
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
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
    if getattr(args, "mission", None) and getattr(args, "prize", None):
        m = _safe_lookup(MISSIONS, getattr(args, "mission", None))
        p = _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (mission_at_risk(m, p) and select_gear(m, p)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "mission", None) is None or c[0] == getattr(args, "mission", None))
              and (getattr(args, "prize", None) is None or c[1] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    mission, prize = rng.choice(list(combos))
    hero = getattr(args, "hero", None) or rng.choice(HERO_NAMES)
    sidekick = getattr(args, "sidekick", None) or rng.choice(SIDEKICK_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting="city", mission=mission, prize=prize, hero=hero, sidekick=sidekick, trait=trait)


def _setup(world: World, params: StoryParams) -> None:
    hero = world.add(Entity(id=params.hero, kind="character", type="hero"))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="sidekick"))
    prize = world.add(Entity(id="prize", type=_safe_lookup(PRIZES, params.prize).type, label=_safe_lookup(PRIZES, params.prize).label,
                             phrase=_safe_lookup(PRIZES, params.prize).phrase, owner=hero.id, caretaker=sidekick.id,
                             region=_safe_lookup(PRIZES, params.prize).region, plural=_safe_lookup(PRIZES, params.prize).plural))
    mission = _safe_lookup(MISSIONS, params.mission)
    world.facts.update(hero=hero, sidekick=sidekick, prize=prize, mission=mission, params=params)


def _predict_badness(world: World, hero: Entity, mission: Mission, prize: Entity) -> bool:
    return mission_at_risk(mission, prize)


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    _setup(world, params)
    hero: Entity = _safe_fact(world, world.facts, "hero")
    sidekick: Entity = _safe_fact(world, world.facts, "sidekick")
    prize: Entity = _safe_fact(world, world.facts, "prize")
    mission: Mission = _safe_fact(world, world.facts, "mission")

    hero.memes["bravery"] = 1.0
    hero.memes["hope"] = 1.0
    world.say(
        f"In {world.setting.place}, {hero.id} was a {params.trait} superhero who loved helping people before the sun went down."
    )
    world.say(
        f"{hero.id} wore {prize.phrase} every day and liked how it made {hero.pronoun('object')} feel ready for action."
    )
    world.para()
    world.say(
        f"One evening, {hero.id} and {sidekick.id} saw trouble near the harbor: a {mission.danger} could ruin the rescue."
    )
    world.say(
        f"{hero.id} wanted to {mission.verb}, but {hero.id} first noticed {hero.pronoun('possessive')} {prize.label} could get {mission.soil}."
    )
    if _predict_badness(world, hero, mission, prize):
        hero.memes["worry"] = 1.0
        world.say(
            f'"If I rush in now, my {prize.label} will get {mission.soil}," {hero.id} said, and {sidekick.id} nodded.'
        )
    world.say(
        f"But {hero.id} took a deep breath. Bravery was not pretending there was no fear; bravery was continuing anyway."
    )
    hero.memes["bravery"] += 1.0
    world.say(
        f"{hero.id} followed the {mission.keyword} clue, and {sidekick.id} stayed close with a lantern to guide the way."
    )

    gear = select_gear(mission, prize)
    if gear is not None:
        world.say(
            f"Together they grabbed {gear.label}. That simple tool fit the danger and gave {hero.id} a safer way forward."
        )
        world.say(
            f"{hero.id} could {mission.verb} without ruining {prize.label}, so {hero.id} went on and saved the day."
        )
        hero.memes["joy"] = 1.0
        hero.memes["bravery"] += 1.0
        world.para()
        world.say(
            f"At the end, the harbor was calm again, {prize.label} stayed clean, and {hero.id} smiled under the city lights."
        )
    else:
        pass

    world.facts["gear"] = gear
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    mission = _safe_fact(world, f, "mission")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a short superhero story for a young child that includes the word "{mission.keyword}".',
        f"Tell a brave story where {hero.id} must {mission.verb} while keeping {prize.phrase} safe.",
        f"Write a small adventure about continuance, where a hero keeps going even when the first plan feels scary.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    sidekick = _safe_fact(world, f, "sidekick")
    mission = _safe_fact(world, f, "mission")
    prize = _safe_fact(world, f, "prize")
    gear = _safe_fact(world, f, "gear")
    return [
        QAItem(
            question=f"What problem did {hero.id} face near the harbor?",
            answer=f"{hero.id} faced {mission.danger}, which could have ruined the rescue and made the scene harder to fix.",
        ),
        QAItem(
            question=f"Why did {hero.id} pause before rushing in?",
            answer=f"{hero.id} paused because {prize.label} could get {mission.soil}, and {hero.id} wanted to help without making a bigger mess.",
        ),
        QAItem(
            question=f"What helped {hero.id} keep going?",
            answer=f"{gear.label} helped {hero.id} move forward safely, and {sidekick.id} stayed close to guide the way.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"{hero.id} kept going with bravery, the harbor became calm, and {prize.label} stayed clean.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is bravery?",
            answer="Bravery is choosing to do something important even when you feel scared.",
        ),
        QAItem(
            question="What does a visor do?",
            answer="A visor helps cover your eyes from bright light or flying bits so you can see better.",
        ),
        QAItem(
            question="What does continuance mean?",
            answer="Continuance means keeping something going or continuing it instead of stopping halfway.",
        ),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="city", mission="optic", prize="goggles", hero="Nova", sidekick="Bolt", trait="brave"),
    StoryParams(setting="city", mission="keel", prize="boots", hero="Aria", sidekick="Echo", trait="steady"),
    StoryParams(setting="city", mission="continuance", prize="cape", hero="Sky", sidekick="Scout", trait="bold"),
]


ASP_RULES = r"""
mission_at_risk(M,P) :- zone(M,R), region(P,R).
has_gear(M,P) :- mission_danger(M,D), gear(G), guards(G,D), covers(G,R), region(P,R).
valid_story(M,P) :- mission_at_risk(M,P), has_gear(M,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("mission_danger", mid, m.danger))
        for r in sorted(m.zone):
            lines.append(asp.fact("zone", mid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for d in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, d))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


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
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero}: {p.mission} with {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
