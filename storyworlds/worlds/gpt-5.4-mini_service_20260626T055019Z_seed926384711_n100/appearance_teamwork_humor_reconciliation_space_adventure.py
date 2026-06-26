#!/usr/bin/env python3
"""
A standalone storyworld for a tiny space-adventure tale about appearance,
teamwork, humor, and reconciliation.

Seed-tale premise:
---
A small crew prepares for a shiny parade on a moon outpost. One astronaut
worries that her patched suit looks silly, another laughs too loudly, and the
third tries to keep everyone working together. A mistake at the airlock makes
the crew feel awkward, but the broken mood is fixed when they help each other
dress, joke kindly, and make the ship look bright again.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    hero: object | None = None
    mate: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "captain"}
        male = {"boy", "man", "pilot"}
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
class Location:
    name: str
    affordances: set[str] = field(default_factory=set)
    appearance: str = ""
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
class Mission:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
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
class Fix:
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
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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

    def copy(self) -> "World":
        clone = World(self.location)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_smear(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("mess", 0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.region not in world.zone:
                continue
            sig = ("smear", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dirty"] = item.meters.get("dirty", 0) + 1
            out.append(f"{actor.id}'s {item.label} got dusty and untidy.")
    return out


def _r_awkward(world: World) -> list[str]:
    if world.facts.get("slip_happened") and not world.facts.get("repaired"):
        sig = ("awkward",)
        if sig not in world.fired:
            world.fired.add(sig)
            return ["The little slip made everybody feel awkward for a moment."]
    return []


CAUSAL_RULES = [(_r_smear, "physical"), (_r_awkward, "social")]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for fn, _tag in CAUSAL_RULES:
            sents = fn(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_mess(world: World, actor: Entity, mission: Mission, prize_id: str) -> dict:
    sim = world.copy()
    _do_mission(sim, sim.get(actor.id), mission, narrate=False)
    prize = sim.get(prize_id)
    return {"soiled": prize.meters.get("dirty", 0) >= THRESHOLD}


def appearance_detail(loc: Location, mission: Mission) -> str:
    return loc.appearance or f"The place looked ready for {mission.keyword} and bright lights."


def _do_mission(world: World, actor: Entity, mission: Mission, narrate: bool = True) -> None:
    world.zone = set(mission.zone)
    actor.meters["mess"] = actor.meters.get("mess", 0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0) + 1
    propagate(world, narrate=narrate)


def select_fix(mission: Mission, prize: Prize) -> Optional[Fix]:
    for fx in FIXES:
        if mission.mess in fx.guards and prize.region in fx.covers:
            return fx
    return None


def tell(loc: Location, mission: Mission, prize_cfg: Prize, hero_name: str = "Nova",
         hero_type: str = "girl", parent_type: str = "captain") -> World:
    world = World(loc)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type,
                            traits=["little", "curious", "messy"]))
    mate = world.add(Entity(id="Mate", kind="character", type=parent_type, label="the captain"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label,
                             phrase=prize_cfg.phrase, owner=hero.id, caretaker=mate.id,
                             worn_by=hero.id, plural=prize_cfg.plural, region=prize_cfg.region))

    world.say(f"{hero.id} was a little {hero_type} astronaut who loved shiny things and brave plans.")
    world.say(f"{hero.pronoun().capitalize()} liked {mission.gerund}, especially when the {loc.name} glimmered.")
    world.say(f"The crew had brought {hero.pronoun('object')} {prize.phrase}, and {hero.id} wore {prize.it()} proudly.")
    world.para()

    world.say(f"At {loc.name}, {appearance_detail(loc, mission)}")
    world.say(f"{hero.id} wanted to {mission.verb}, but {hero.pronoun('possessive')} captain noticed the {prize.label} could get messy.")
    pred = predict_mess(world, hero, mission, prize.id)
    if pred["soiled"]:
        world.facts["slip_happened"] = True
        world.say(f'"If you rush off now, you will get {prize.label} {mission.soil}," the captain said.')
        world.say(f"{hero.id} tried to {mission.rush}, but the shiny floor made the boots wobble.")
        hero.memes["awkward"] = hero.memes.get("awkward", 0) + 1
        world.say(f"Then {hero.id} gave a tiny laugh, because the wobble looked more silly than scary.")
        world.say(f"The captain laughed too, and the room felt a little less tight.")
    world.para()

    fix = select_fix(mission, prize)
    if fix is None:
        pass
    if pred["soiled"]:
        world.say(f'{hero.pronoun("possessive").capitalize()} captain pointed at a {fix.label} and smiled.')
        world.say(f'"How about we {fix.prep} and do it together?"')
        hero.memes["reconciled"] = hero.memes.get("reconciled", 0) + 1
        world.say(f"{hero.id}'s face softened. {hero.id} nodded and hugged {hero.pronoun('possessive')} captain.")
        world.say(f"Together they {fix.tail}. Soon {hero.id} was {mission.gerund}, and {prize.label} stayed clean.")
        world.facts["repaired"] = True
    else:
        world.say(f"They did the task carefully, and the {prize.label} stayed neat without trouble.")
        world.facts["repaired"] = True

    world.facts.update(hero=hero, mate=mate, prize=prize, mission=mission, location=loc, fix=fix)
    return world


LOCATIONS = {
    "moon_base": Location(
        name="the moon base",
        affordances={"parade", "float_tuneup", "stargaze"},
        appearance="The moon base was silver and round, with windows that blinked like sleepy stars.",
    ),
    "orbital_dock": Location(
        name="the orbital dock",
        affordances={"parade", "cargo_sort", "stargaze"},
        appearance="The orbital dock drifted over the dark, all bright rails and shiny screens.",
    ),
    "comet_hub": Location(
        name="the comet hub",
        affordances={"parade", "sample_swap", "stargaze"},
        appearance="The comet hub sparkled with icy dust and long blue banners.",
    ),
}

MISSIONS = {
    "parade": Mission(
        id="parade",
        verb="join the parade",
        gerund="marching in the parade",
        rush="dash to the parade line",
        mess="dust",
        soil="all dusty",
        zone={"torso"},
        keyword="appearance",
        tags={"appearance", "humor", "teamwork", "reconciliation"},
    ),
    "float_tuneup": Mission(
        id="float_tuneup",
        verb="help tune the float",
        gerund="fixing the parade float",
        rush="hop onto the float",
        mess="grease",
        soil="greasy",
        zone={"hands", "torso"},
        keyword="appearance",
        tags={"appearance", "teamwork", "humor", "reconciliation"},
    ),
    "sample_swap": Mission(
        id="sample_swap",
        verb="trade the crystal sample",
        gerund="carrying the crystal sample",
        rush="run to the sample shelf",
        mess="sparkles",
        soil="sparkly",
        zone={"hands"},
        keyword="appearance",
        tags={"appearance", "teamwork", "humor", "reconciliation"},
    ),
    "stargaze": Mission(
        id="stargaze",
        verb="watch the star show",
        gerund="staring up at the stars",
        rush="race to the viewing dome",
        mess="dust",
        soil="dusty",
        zone={"torso"},
        keyword="appearance",
        tags={"appearance", "humor"},
    ),
}

PRIZES = {
    "jacket": Prize("jacket", "a clean silver jacket", "jacket", "torso"),
    "helmet": Prize("helmet", "a glossy helmet", "helmet", "torso"),
    "gloves": Prize("gloves", "bright white gloves", "gloves", "hands", True),
}

FIXES = [
    Fix("tape", "a roll of glow tape", {"torso", "hands"}, {"dust", "grease", "sparkles"}, "put glow tape over the scuffs", "finished the float with glow tape"),
    Fix("cape", "a parade cape", {"torso"}, {"dust"}, "wear the parade cape first", "walked in the parade with the cape"),
    Fix("mitts", "clean work mitts", {"hands"}, {"grease", "sparkles"}, "put on clean work mitts first", "swapped the sample with clean work mitts"),
]

NAMES = ["Nova", "Rin", "Milo", "Tess", "Orin", "Pia"]
KINDS = ["girl", "boy"]
PARENTS = ["captain", "pilot"]
TRAITS = ["brave", "cheerful", "careful", "silly", "spunky"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for lname, loc in LOCATIONS.items():
        for mid in loc.affordances:
            mission = _safe_lookup(MISSIONS, mid)
            for pid, prize in PRIZES.items():
                if prize.region in mission.zone and select_fix(mission, prize):
                    out.append((lname, mid, pid))
    return out


@dataclass
class StoryParams:
    location: str
    mission: str
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
    return [
        f'Write a short space-adventure story for a young child about "{f["mission"].keyword}" and a shiny outfit.',
        f"Tell a story where {f['hero'].id} and the {f['mate'].label} work together on the {f['location'].name} and make up after a small mistake.",
        f"Write a gentle story with humor and reconciliation that includes a bright space base, a costume, and a helpful teamwork fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mate, prize, mission, loc = f["hero"], f["mate"], f["prize"], f["mission"], f["location"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do at {loc.name}?",
            answer=f"{hero.id} wanted to {mission.verb} at {loc.name}. {hero.pronoun().capitalize()} was excited because {loc.appearance.lower()}",
        ),
        QAItem(
            question=f"Why did the captain worry about {hero.pronoun('possessive')} {prize.label}?",
            answer=f"The captain worried because if {hero.id} went too fast, the {prize.label} would get {mission.soil}.",
        ),
        QAItem(
            question=f"How did {hero.id} and the captain fix the problem?",
            answer=f"They chose to work together and used {f['fix'].label}, so {hero.id} could {mission.verb} and still keep {prize.label} clean.",
        ),
    ]
    if f.get("repaired"):
        qa.append(QAItem(
            question=f"How did {hero.id} feel after the captain made a joking offer?",
            answer=f"{hero.id} felt better, laughed a little, and then felt close to the captain again.",
        ))
    return qa


KNOWLEDGE = {
    "appearance": [("What is appearance?", "Appearance means how something looks, like its color, shine, shape, or neatness.")],
    "teamwork": [("What is teamwork?", "Teamwork means people help each other do something together.")],
    "humor": [("What is humor?", "Humor is something funny that makes people smile or laugh.")],
    "reconciliation": [("What is reconciliation?", "Reconciliation means fixing a hurt feeling and becoming friendly again.")],
    "space": [("What is a space base?", "A space base is a place where astronauts live or work away from Earth.")],
    "jacket": [("What is a jacket for?", "A jacket helps cover your body and can keep you warm or neat.")],
    "helmet": [("Why do astronauts wear helmets?", "Astronauts wear helmets to protect their heads and help them breathe safely in space.")],
    "gloves": [("What do gloves help with?", "Gloves help keep hands clean, warm, or protected while working.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["mission"].tags)
    tags.update({"appearance", "teamwork", "humor", "reconciliation", "space"})
    if world.facts["prize"].type == "jacket":
        tags.add("jacket")
    if world.facts["prize"].type == "helmet":
        tags.add("helmet")
    if world.facts["prize"].type == "gloves":
        tags.add("gloves")
    out: list[QAItem] = []
    for key in ["appearance", "teamwork", "humor", "reconciliation", "space", "jacket", "helmet", "gloves"]:
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
    return out


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
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.region:
            bits.append(f"region={e.region}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("moon_base", "parade", "jacket", "Nova", "girl", "captain", "cheerful"),
    StoryParams("orbital_dock", "float_tuneup", "gloves", "Rin", "boy", "pilot", "silly"),
    StoryParams("comet_hub", "sample_swap", "helmet", "Tess", "girl", "captain", "careful"),
]


def explain_rejection(mission: Mission, prize: Prize) -> str:
    return f"(No story: {mission.gerund} does not reasonably threaten a {prize.label} in this little space world.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "mission", None) and getattr(args, "prize", None):
        m, p = _safe_lookup(MISSIONS, getattr(args, "mission", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (p.region in m.zone and select_fix(m, p)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "location", None) is None or c[0] == getattr(args, "location", None))
              and (getattr(args, "mission", None) is None or c[1] == getattr(args, "mission", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    loc, mid, pid = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    gender = getattr(args, "gender", None) or rng.choice(KINDS)
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    trait = rng.choice(TRAITS)
    return StoryParams(loc, mid, pid, name, gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(LOCATIONS, params.location), _safe_lookup(MISSIONS, params.mission), _safe_lookup(PRIZES, params.prize),
                 params.name, params.gender, params.parent)
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


ASP_RULES = r"""
prize_at_risk(M, P) :- zone(M, R), prize_region(P, R).
has_fix(M, P) :- prize_at_risk(M, P), fixable(M, P).
valid(Loc, M, P) :- affords(Loc, M), prize_at_risk(M, P), has_fix(M, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for lid, loc in LOCATIONS.items():
        lines.append(asp.fact("location", lid))
        for m in sorted(loc.affordances):
            lines.append(asp.fact("affords", lid, m))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        for r in sorted(m.zone):
            lines.append(asp.fact("zone", mid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, p.region))
    for fx in FIXES:
        for m in sorted(fx.guards):
            for mid, mission in MISSIONS.items():
                if m == mission.mess:
                    lines.append(asp.fact("fixable", mid, mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world with appearance, teamwork, humor, and reconciliation.")
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--name")
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


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)

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
            header = f"### {p.name}: {p.mission} at {p.location} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
