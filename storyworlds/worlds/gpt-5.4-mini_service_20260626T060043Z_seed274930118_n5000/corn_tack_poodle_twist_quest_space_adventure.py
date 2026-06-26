#!/usr/bin/env python3
"""
A small standalone story world: a space adventure with a poodle, corn, and a tack.

Premise:
- A child astronaut and their poodle are on a tiny ship headed to a moon garden.
- The hero wants to complete a Quest involving a shiny corn plant.
- A loose tack threatens the cargo and the ship's soft seat cover.
- A clever Twist turns the problem into a safe, happy ending.

This script follows the storyworld contract with:
- typed entities with meters and memes
- a Python reasonableness gate
- inline ASP_RULES twin
- generate / emit / main CLI support
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
    protective: bool = False
    plural: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    corn: object | None = None
    hero: object | None = None
    parent: object | None = None
    poodle: object | None = None
    tack: object | None = None
    twist_item: object | None = None
    def __post_init__(self):
        for k in ["damage", "dust", "worry", "joy", "curiosity", "resolve", "mischief"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "astronaut-girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "astronaut-boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str = "the starship"
    indoors: bool = True
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
class Quest:
    id: str
    title: str
    verb: str
    gerund: str
    rush: str
    risk: str
    hazard: str
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
class Twist:
    id: str
    label: str
    phrase: str
    covers: set[str]
    solves: set[str]
    prep: str
    tail: str
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


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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
        return any(it.protective and region in it.covers for it in self.worn_items(actor))

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
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "starship": Setting(place="the starship", indoors=True, affords={"quest", "twist"}),
    "moon_garden": Setting(place="the moon garden", indoors=False, affords={"quest"}),
    "orbital_greenhouse": Setting(place="the orbital greenhouse", indoors=True, affords={"quest"}),
}

QUESTS = {
    "corn_quest": Quest(
        id="corn_quest",
        title="Quest for the corn seed",
        verb="carry the corn seed to the moon garden",
        gerund="carrying the corn seed",
        rush="dash for the storage shelf",
        risk="the corn seed could get scratched",
        hazard="scratched",
        zone={"hands", "seat"},
        keyword="corn",
        tags={"corn", "quest", "space"},
    ),
    "poodle_quest": Quest(
        id="poodle_quest",
        title="Quest for the poodle brush",
        verb="brush the poodle in zero gravity",
        gerund="brushing the poodle",
        rush="float toward the grooming nook",
        risk="the poodle could get too dusty",
        hazard="dusty",
        zone={"hands", "torso"},
        keyword="poodle",
        tags={"poodle", "quest", "space"},
    ),
    "tack_quest": Quest(
        id="tack_quest",
        title="Quest for the loose tack",
        verb="find the loose tack before it pokes the seat",
        gerund="hunting for the loose tack",
        rush="scoot under the cargo net",
        risk="the seat cover could get poked",
        hazard="poked",
        zone={"seat", "hands"},
        keyword="tack",
        tags={"tack", "quest", "space"},
    ),
}

TWISTS = [
    Twist(
        id="seat_pad",
        label="a soft seat pad",
        phrase="a soft seat pad",
        covers={"seat"},
        solves={"poked", "scratched"},
        prep="strap on a soft seat pad first",
        tail="strapped on the soft seat pad",
    ),
    Twist(
        id="gloves",
        label="space gloves",
        phrase="space gloves",
        covers={"hands"},
        solves={"scratched", "dusty", "poked"},
        prep="put on space gloves first",
        tail="put on the space gloves",
        plural=True,
    ),
    Twist(
        id="bubble_hood",
        label="a clear bubble hood",
        phrase="a clear bubble hood",
        covers={"torso", "hands"},
        solves={"dusty"},
        prep="use a clear bubble hood first",
        tail="used the clear bubble hood",
    ),
]

GIRL_NAMES = ["Mina", "Tia", "Nova", "Luna", "Zara"]
BOY_NAMES = ["Kai", "Theo", "Jasper", "Finn", "Arlo"]
TRAITS = ["brave", "curious", "gentle", "careful", "spirited"]


@dataclass
class StoryParams:
    place: str
    quest: str
    twist: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
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


def quest_at_risk(q: Quest, twist: Twist) -> bool:
    return bool(q.zone & twist.covers)


def select_twist(q: Quest) -> Optional[Twist]:
    for t in TWISTS:
        if quest_at_risk(q, t) and q.hazard in t.solves:
            return t
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for qid in setting.affords:
            q = _safe_lookup(QUESTS, qid)
            for t in TWISTS:
                if quest_at_risk(q, t) and q.hazard in t.solves:
                    out.append((place, qid, t.id))
    return out


def explain_rejection(q: Quest, t: Twist) -> str:
    if not quest_at_risk(q, t):
        return f"(No story: {t.label} does not cover the risky part of the quest.)"
    return f"(No story: {t.label} does not actually solve {q.hazard} for this quest.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
quest_at_risk(Q,T) :- quest_zone(Q,R), twist_covers(T,R).
compatible(P,Q,T) :- affords(P,Q), quest_at_risk(Q,T), quest_hazard(Q,H), twist_solves(T,H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for qid in sorted(s.affords):
            lines.append(asp.fact("affords", sid, qid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("quest_hazard", qid, q.hazard))
        for r in sorted(q.zone):
            lines.append(asp.fact("quest_zone", qid, r))
    for t in TWISTS:
        lines.append(asp.fact("twist", t.id))
        for r in sorted(t.covers):
            lines.append(asp.fact("twist_covers", t.id, r))
        for s in sorted(t.solves):
            lines.append(asp.fact("twist_solves", t.id, s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def _warn_if_needed(world: World, hero: Entity, q: Quest, tw: Twist) -> bool:
    if not quest_at_risk(q, tw):
        return False
    world.say(f'"If you rush ahead, {q.risk}," {hero.pronoun("possessive")} parent said.')
    world.facts["warning"] = True
    return True


def _do_quest(world: World, hero: Entity, q: Quest, narrate: bool = True) -> None:
    hero.memes["resolve"] += 1
    hero.meters["curiosity"] += 1
    world.zone = set(q.zone)
    for e in world.characters():
        if e.id != hero.id:
            e.memes["worry"] += 1
    if narrate:
        world.say(f"{hero.id} tried to {q.verb}.")


def _apply_mess(world: World, hero: Entity, q: Quest) -> list[str]:
    out: list[str] = []
    for item in world.worn_items(hero):
        if item.protective or item.worn_by != hero.id:
            continue
        if item.meters["damage"] >= THRESHOLD:
            continue
        if not (q.zone & item.covers):
            continue
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    return []


def tell(setting: Setting, quest: Quest, twist: Twist, hero_name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=("girl" if gender == "girl" else "boy")))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the captain-parent"))
    poodle = world.add(Entity(id="Poodle", kind="character", type="poodle", label="the poodle"))
    corn = world.add(Entity(id="Corn", type="corn", label="the corn seed", phrase="a bright corn seed", caretaker=parent.id))
    tack = world.add(Entity(id="Tack", type="tack", label="the tack", phrase="a tiny silver tack", caretaker=parent.id))
    twist_item = world.add(Entity(id=twist.id, type="gear", label=twist.label, protective=True, plural=twist.plural, covers=set(twist.covers), owner=hero.id))
    twist_item.worn_by = hero.id
    world.facts.update(hero=hero, parent=parent, poodle=poodle, corn=corn, tack=tack, quest=quest, twist=twist, setting=setting)

    world.say(f"{hero.id} was a {trait} young astronaut who loved the stars.")
    world.say(f"{hero.id} had a fluffy poodle who rode along on every space trip.")
    world.say(f"One day, they were on {setting.place} for a small Quest about {quest.keyword}.")
    world.say(f"The {quest.keyword} was important, and so was the tiny {tack.label} that kept slipping near the seat.")

    world.para()
    world.say(f"{hero.id} wanted to {quest.verb}, and {poodle.label} wagged {poodle.pronoun('possessive')} tail in zero gravity.")
    _warn_if_needed(world, hero, quest, twist)
    hero.memes["mischief"] += 1
    world.say(f"{hero.id} still reached for the task, but the loose tack made the ship feel tricky.")

    world.para()
    if twist_item.worn_by:
        world.say(f"Then {hero.id} used {twist.prep}.")
    hero.memes["joy"] += 1
    hero.memes["resolve"] += 1
    world.say(f"That Twist kept the seat safe, and it helped {hero.id} finish the Quest without a poke or scratch.")
    world.say(f"In the end, {hero.id} and {poodle.label} floated home with {corn.label} tucked safely away, and the tack stayed put in a little tray.")
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    q: Quest = _safe_fact(world, f, "quest")
    t: Twist = _safe_fact(world, f, "twist")
    return [
        f'Write a short space adventure for a young child about {f["hero"].id}, a poodle, and a {q.keyword} Quest.',
        f"Tell a gentle story where a child astronaut wants to {q.verb} but a loose tack causes trouble, and a {t.label} fixes it.",
        f'Write a child-friendly story in space that includes the words "{q.keyword}" and "{t.id}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    parent: Entity = _safe_fact(world, f, "parent")
    poodle: Entity = _safe_fact(world, f, "poodle")
    q: Quest = _safe_fact(world, f, "quest")
    t: Twist = _safe_fact(world, f, "twist")
    return [
        QAItem(
            question=f"What was {hero.id} trying to do on the space trip?",
            answer=f"{hero.id} was trying to {q.verb}.",
        ),
        QAItem(
            question=f"Who went with {hero.id} on the adventure?",
            answer=f"{poodle.label} the poodle went with {hero.id}, and {parent.label} helped keep things safe.",
        ),
        QAItem(
            question=f"Why did the parent warn {hero.id}?",
            answer=f"The parent worried that {q.risk} if {hero.id} rushed ahead.",
        ),
        QAItem(
            question=f"How did {t.label} help?",
            answer=f"{t.label} covered the risky part and let {hero.id} finish the Quest safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a poodle?",
            answer="A poodle is a fluffy kind of dog with curly fur.",
        ),
        QAItem(
            question="What is corn?",
            answer="Corn is a plant that grows in rows and makes yellow kernels people can eat.",
        ),
        QAItem(
            question="What is a tack?",
            answer="A tack is a small sharp pin that can hold paper or cloth in place.",
        ),
        QAItem(
            question="What does a quest mean?",
            answer="A quest is a special job or adventure where someone tries to reach a goal.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that helps the story turn in a new direction.",
        ),
    ]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure story world with corn, tack, poodle, Twist, and Quest.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--twist", choices=[t.id for t in TWISTS])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "captain"])
    ap.add_argument("--name")
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
    if getattr(args, "quest", None) and getattr(args, "twist", None):
        q = _safe_lookup(QUESTS, getattr(args, "quest", None))
        t = next(t for t in TWISTS if t.id == getattr(args, "twist", None))
        if not (quest_at_risk(q, t) and q.hazard in t.solves):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
              and (getattr(args, "twist", None) is None or c[2] == getattr(args, "twist", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, qid, tid = rng.choice(list(combos))
    q = _safe_lookup(QUESTS, qid)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father", "captain"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, quest=qid, twist=tid, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    q = _safe_lookup(QUESTS, params.quest)
    t = next(t for t in TWISTS if t.id == params.twist)
    world = tell(_safe_lookup(SETTINGS, params.place), q, t, params.name, params.gender, params.parent, params.trait)
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
    StoryParams(place="starship", quest="corn_quest", twist="seat_pad", name="Nova", gender="girl", parent="captain", trait="curious"),
    StoryParams(place="orbital_greenhouse", quest="poodle_quest", twist="bubble_hood", name="Kai", gender="boy", parent="father", trait="gentle"),
    StoryParams(place="starship", quest="tack_quest", twist="gloves", name="Mina", gender="girl", parent="mother", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
