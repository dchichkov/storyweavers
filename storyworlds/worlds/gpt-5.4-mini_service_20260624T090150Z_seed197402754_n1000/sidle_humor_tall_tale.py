#!/usr/bin/env python3
"""
storyworlds/worlds/sidle_humor_tall_tale.py
===========================================

A small, humorous tall-tale story world about sidling past trouble.

Premise:
- A character wants to sidle around a big, stubborn obstacle.
- Their first attempt is too obvious and wakes the trouble.
- A playful exaggeration, a clever helper, or a ridiculous tool turns the
  moment into a funny success.

The world keeps a live simulation with physical meters and emotional memes.
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

    region: object | None = None
    h: object | None = None
    hero: object | None = None
    problem: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
class Setting:
    place: str
    indoors: bool
    affords: set[str] = field(default_factory=set)
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
class Move:
    id: str
    verb: str
    gerund: str
    sidle_line: str
    mess: str
    zone: set[str]
    weather: str
    tall_tail: str
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
class Problem:
    id: str
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
class Helper:
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
        self.zone: set[str] = set()
        self.weather: str = ""
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

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


MESSY = {"dusty", "sticky", "muddy", "soggy", "painted"}


def _r_spoil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in MESSY:
            if actor.meters.get(mess, 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.region not in world.zone:
                    continue
                sig = ("spoil", actor.id, item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] = item.meters.get(mess, 0.0) + 1
                item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
                out.append(f"{item.label.capitalize()} got {mess}.")
    return out


def _r_work(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters.get("dirty", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] = carer.meters.get("workload", 0.0) + 1
        out.append(f"That would mean more work for {carer.label}.")
    return out


def _r_slip_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes.get("slipped", 0.0) < THRESHOLD or actor.memes.get("stubborn", 0.0) < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["frustration"] = actor.memes.get("frustration", 0.0) + 1
        return ["__conflict__"]
    return []


CAUSAL_RULES = [
    _r_spoil,
    _r_work,
    _r_slip_conflict,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def risk_check(move: Move, problem: Problem) -> bool:
    return problem.region in move.zone


def pick_helper(move: Move, problem: Problem) -> Optional[Helper]:
    for helper in HELPERS:
        if move.mess in helper.guards and problem.region in helper.covers:
            return helper
    return None


def predict_mess(world: World, actor: Entity, move: Move, problem_id: str) -> dict:
    sim = world.copy()
    _do_move(sim, sim.get(actor.id), move, narrate=False)
    problem = sim.entities.get(problem_id)
    return {"spoiled": bool(problem and problem.meters.get("dirty", 0.0) >= THRESHOLD),
            "workload": sum(e.meters.get("workload", 0.0) for e in sim.characters())}


def _do_move(world: World, actor: Entity, move: Move, narrate: bool = True) -> None:
    if move.id not in world.setting.affords:
        return
    world.zone = set(move.zone)
    actor.meters[move.mess] = actor.meters.get(move.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.meters.keys() if t.startswith("trait:")), "")
    world.say(
        f"{hero.id} was a little {hero.type} with a grin as wide as the county road, "
        f"and {hero.pronoun('possessive')} feet could sidle quieter than a cat on a quilt."
    )


def loves(world: World, hero: Entity, move: Move) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    where = "inside" if world.setting.indoors else "out on the prairie"
    world.say(
        f"{hero.pronoun().capitalize()} loved to {move.verb} {where}; "
        f"{move.gerund} made the day feel big enough to wear a hat on."
    )


def setup_problem(world: World, hero: Entity, caretaker: Entity, problem: Problem) -> None:
    world.say(
        f"One day, {hero.id} found {hero.pronoun('possessive')} {problem.label} sitting there like a "
        f"stubborn old stump in a thunderstorm."
    )
    world.say(
        f"{caretaker.label.capitalize()} had just polished it, and it looked bright enough to outshine a barn roof at noon."
    )


def wants(world: World, hero: Entity, move: Move) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(
        f"{hero.id} wanted to {move.verb}, but first {hero.pronoun('subject')} tried to sidle close and be sneaky about it."
    )


def warn(world: World, caretaker: Entity, hero: Entity, move: Move, problem: Problem) -> bool:
    pred = predict_mess(world, hero, move, problem.id)
    if not pred["spoiled"]:
        return False
    world.facts["predicted_workload"] = pred["workload"]
    world.say(
        f'"If you go on and {move.verb}," {caretaker.label} said, '
        f'"your {problem.label} will get {move.mess}.'
    )
    return True


def slip(world: World, hero: Entity, move: Move) -> None:
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 1
    hero.memes["slipped"] = hero.memes.get("slipped", 0.0) + 1
    world.say(
        f"{hero.id} still gave it a try and {move.sidle_line}, but {hero.pronoun('subject')} slipped on a patch of common sense."
    )


def giggle(world: World, hero: Entity, move: Move) -> None:
    if hero.memes.get("frustration", 0.0) >= THRESHOLD:
        world.say(
            f"{hero.id} puffed {hero.pronoun('possessive')} cheeks and made a face so funny a fencepost would have laughed."
        )


def offer_helper(world: World, caretaker: Entity, hero: Entity, move: Move, problem: Problem) -> Optional[Helper]:
    helper = pick_helper(move, problem)
    if helper is None:
        return None
    h = world.add(Entity(
        id=helper.id,
        type="helper",
        label=helper.label,
        owner=hero.id,
        caretaker=caretaker.id,
        plural=helper.plural,
    ))
    h.worn_by = hero.id
    if predict_mess(world, hero, move, problem.id)["spoiled"]:
        h.worn_by = None
        del world.entities[h.id]
        return None
    world.say(
        f"{caretaker.label.capitalize()} scratched {caretaker.pronoun('possessive')} head, then said, "
        f'"How about we {helper.prep}?"'
    )
    return helper


def accept(world: World, caretaker: Entity, hero: Entity, move: Move, problem: Problem, helper: Helper) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    hero.memes["frustration"] = 0.0
    world.say(
        f"{hero.id} lit up like a lantern in a lightning storm and hugged {caretaker.pronoun('object')}."
    )
    world.say(
        f"They {helper.tail}. Soon {hero.id} was {move.gerund}, {problem.label} stayed clean, and the whole scene looked as grand as a parade pulled by geese."
    )


def tell(setting: Setting, move: Move, problem_cfg: Problem,
         hero_name: str = "Milo", hero_type: str = "boy",
         parent_type: str = "father") -> World:
    world = World(setting)
    world.weather = "" if setting.indoors else move.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    hero.meters["trait:humor"] = 1
    caretaker = world.add(Entity(id="Caretaker", kind="character", type=parent_type, label="the caretaker"))
    problem = world.add(Entity(
        id=problem_cfg.id, type=problem_cfg.type, label=problem_cfg.label,
        phrase=problem_cfg.phrase, owner=hero.id, caretaker=caretaker.id,
        region=problem_cfg.region, plural=problem_cfg.plural,
    ))

    introduce(world, hero)
    loves(world, hero, move)
    setup_problem(world, hero, caretaker, problem)
    world.para()
    wants(world, hero, move)
    warn(world, caretaker, hero, move, problem)
    slip(world, hero, move)
    world.para()
    giggle(world, hero, move)
    helper = offer_helper(world, caretaker, hero, move, problem)
    if helper:
        accept(world, caretaker, hero, move, problem, helper)

    world.facts.update(hero=hero, caretaker=caretaker, problem=problem, move=move,
                       helper=helper, setting=setting)
    return world


SETTINGS = {
    "barn": Setting(place="the barn", indoors=True, affords={"sidle_bale", "sidle_gate", "sidle_jar"}),
    "porch": Setting(place="the porch", indoors=False, affords={"sidle_bale", "sidle_gate"}),
    "kitchen": Setting(place="the kitchen", indoors=True, affords={"sidle_jar"}),
}

MOVES = {
    "sidle_bale": Move(
        id="sidle_bale",
        verb="sidle past the hay bale",
        gerund="sidling past the hay bale",
        sidle_line="sidled sideways like a crab with manners",
        mess="dusty",
        zone={"feet", "legs"},
        weather="",
        tall_tail="sidled past the hay bale without waking a rooster the size of a wagon",
        keyword="sidle",
        tags={"dust", "barn"},
    ),
    "sidle_gate": Move(
        id="sidle_gate",
        verb="sidle past the gate",
        gerund="sidling past the gate",
        sidle_line="sidled along the fence as careful as a moonbeam",
        mess="muddy",
        zone={"feet"},
        weather="rainy",
        tall_tail="sidled past the gate while the mud grumbled underneath",
        keyword="sidle",
        tags={"mud", "gate"},
    ),
    "sidle_jar": Move(
        id="sidle_jar",
        verb="sidle around the jelly jar",
        gerund="sidling around the jelly jar",
        sidle_line="sidled around it so gently even the spoon held its breath",
        mess="sticky",
        zone={"hands", "torso"},
        weather="",
        tall_tail="sidled around the jelly jar and kept the kitchen from sticking to itself",
        keyword="sidle",
        tags={"jelly", "kitchen"},
    ),
}

PROBLEMS = {
    "hat": Problem(
        id="hat",
        label="tall hat",
        phrase="a tall hat with a shiny ribbon",
        type="hat",
        region="head",
    ),
    "boots": Problem(
        id="boots",
        label="Sunday boots",
        phrase="Sunday boots with bright buckles",
        type="boots",
        region="feet",
        plural=True,
    ),
    "jelly": Problem(
        id="jelly",
        label="jelly jar",
        phrase="a jelly jar full of gooseberry jam",
        type="jar",
        region="hands",
    ),
}

HELPERS = [
    Helper(
        id="dust_cap",
        label="a dust cap",
        covers={"head"},
        guards={"dusty"},
        prep="put on a dust cap first",
        tail="put on the dust cap and sidled back through the barn",
    ),
    Helper(
        id="mud_boots",
        label="mud boots",
        covers={"feet"},
        guards={"muddy"},
        prep="pull on the mud boots first",
        tail="pulled on the mud boots and sidled back to the gate",
        plural=True,
    ),
    Helper(
        id="dish_gloves",
        label="dish gloves",
        covers={"hands"},
        guards={"sticky"},
        prep="wear dish gloves first",
        tail="wore the dish gloves and sidled around the jelly jar",
        plural=True,
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for move_id in setting.affords:
            move = _safe_lookup(MOVES, move_id)
            for prob_id, prob in PROBLEMS.items():
                if risk_check(move, prob) and pick_helper(move, prob):
                    combos.append((place, move_id, prob_id))
    return combos


@dataclass
class StoryParams:
    place: str
    move: str
    problem: str
    name: str
    gender: str
    caretaker: str
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


KNOWLEDGE = {
    "sidle": [
        ("What does it mean to sidle?", "To sidle means to move slowly and a little sideways, usually to avoid notice or squeeze past something carefully."),
    ],
    "dust": [
        ("What is dust?", "Dust is made of tiny dry bits of dirt, cloth, and other little pieces that can float or settle on things."),
    ],
    "mud": [
        ("What is mud?", "Mud is soft, wet dirt that can cling to shoes and make a mess."),
    ],
    "sticky": [
        ("Why is jelly sticky?", "Jelly is sticky because it is thick and sugary, so it can cling to hands and jars."),
    ],
    "hat": [
        ("What is a hat for?", "A hat can keep the sun off your head or just make you look fancy."),
    ],
    "boots": [
        ("What are boots for?", "Boots protect your feet and help you walk in mud or puddles."),
    ],
    "gloves": [
        ("What are gloves for?", "Gloves cover your hands to keep them clean or warm."),
    ],
}
KNOWLEDGE_ORDER = ["sidle", "dust", "mud", "sticky", "hat", "boots", "gloves"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short tall-tale story for a little child about "{f["move"].keyword}" and a funny sideways try.',
        f"Tell a humorous story where {f['hero'].id} wants to {f['move'].verb} but {f['caretaker'].label} worries about the {f['problem'].label}.",
        f'Write a child-friendly tall tale that includes the word "{f["move"].keyword}" and ends with a silly, safe fix.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, caretaker, problem, move = f["hero"], f["caretaker"], f["problem"], f["move"]
    helper = f.get("helper")
    return [
        QAItem(
            question=f"Who wanted to {move.verb} in the story?",
            answer=f"{hero.id} wanted to {move.verb}, and {hero.pronoun('subject')} tried to do it as quietly as a cat tiptoeing through cornmeal.",
        ),
        QAItem(
            question=f"Why did {caretaker.label} worry about the {problem.label}?",
            answer=f"{caretaker.label.capitalize()} worried because the {problem.label} could get {move.mess} if {hero.id} went on without a better plan.",
        ),
        QAItem(
            question=f"What funny thing happened before the ending?",
            answer=f"{hero.id} tried to sidle along, slipped in a way that would make a rooster snort, and then everybody had to look for a better idea.",
        ),
    ] + ([
        QAItem(
            question=f"How did {helper.label} help the story end well?",
            answer=f"They used {helper.label} so {hero.id} could {move.verb} without ruining the {problem.label}, and that made the whole plan work.",
        ),
        QAItem(
            question=f"How did {hero.id} feel when the helper plan worked?",
            answer=f"{hero.id} felt happy and mighty proud, like somebody who had just outrun a freight train on a tricycle.",
        ),
    ] if helper else [])


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["move"].tags)
    if world.facts.get("helper"):
        tags.update({"boots", "gloves", "hat"})
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge Q&A ==")
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({x[0] for x in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="barn", move="sidle_bale", problem="hat", name="Mabel", gender="girl", caretaker="mother"),
    StoryParams(place="porch", move="sidle_gate", problem="boots", name="Hank", gender="boy", caretaker="father"),
    StoryParams(place="kitchen", move="sidle_jar", problem="jelly", name="Nora", gender="girl", caretaker="mother"),
]


ASP_RULES = r"""
risk(Move, Problem) :- zone(Move, Region), region(Problem, Region).
fix(Helper, Move, Problem) :- risk(Move, Problem), helper(Helper),
                              guards(Helper, Mess), mess(Move, Mess),
                              covers(Helper, Region), region(Problem, Region).
valid(Place, Move, Problem) :- affords(Place, Move), risk(Move, Problem), fix(_, Move, Problem).
valid_story(Place, Move, Problem, Gender) :- valid(Place, Move, Problem), genders(Problem, Gender).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoors:
            lines.append(asp.fact("indoors", pid))
        for m in sorted(s.affords):
            lines.append(asp.fact("affords", pid, m))
    for mid, m in MOVES.items():
        lines.append(asp.fact("move", mid))
        lines.append(asp.fact("mess", mid, m.mess))
        for z in sorted(m.zone):
            lines.append(asp.fact("zone", mid, z))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("region", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("genders", pid, g))
    for h in HELPERS:
        lines.append(asp.fact("helper", h.id))
        for g in sorted(h.guards):
            lines.append(asp.fact("guards", h.id, g))
        for c in sorted(h.covers):
            lines.append(asp.fact("covers", h.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    a, p = set(asp_valid_combos()), set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A humorous tall-tale story world about sidling.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caretaker", choices=["mother", "father"])
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
    if getattr(args, "move", None) and getattr(args, "problem", None):
        mv, pr = _safe_lookup(MOVES, getattr(args, "move", None)), _safe_lookup(PROBLEMS, getattr(args, "problem", None))
        if not (risk_check(mv, pr) and pick_helper(mv, pr)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "move", None) is None or c[1] == getattr(args, "move", None))
              and (getattr(args, "problem", None) is None or c[2] == getattr(args, "problem", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, move_id, problem_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(["Mabel", "Hank", "Nora", "Otis", "June", "Eli"])
    caretaker = getattr(args, "caretaker", None) or rng.choice(["mother", "father"])
    return StoryParams(place=place, move=move_id, problem=problem_id, name=name, gender=gender, caretaker=caretaker)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(MOVES, params.move), _safe_lookup(PROBLEMS, params.problem),
                 hero_name=params.name, hero_type=params.gender, parent_type=params.caretaker)
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
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, move, problem) combos ({len(stories)} with gender):\n")
        for place, move, problem in triples:
            genders = sorted(g for (pl, mv, pr, g) in stories if (pl, mv, pr) == (place, move, problem))
            print(f"  {place:8} {move:12} {problem:8}  [{', '.join(genders)}]")
        return

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
            header = f"### {p.name}: {p.move} at {p.place} (problem: {p.problem})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
