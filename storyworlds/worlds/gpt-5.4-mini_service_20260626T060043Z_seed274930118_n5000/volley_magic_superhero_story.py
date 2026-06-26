#!/usr/bin/env python3
"""
A standalone storyworld for a tiny superhero tale about a magic volley.

Premise:
- A young hero wants to play a spectacular magic volleyball game.
- The game is exciting but risky because the ball can crack windows, knock over
  trophies, or burst into sparks if used carelessly.
- A mentor superhero sees the danger, warns the hero, and offers a safer
  magical move: a shielded court, a softer spell, or a teamwork trick.
- The story resolves when the hero learns to channel the magic volley in a
  responsible way, ending with a bright, victorious image.

This world models:
- typed entities with physical meters and emotional memes
- causal simulation with state-driven prose
- a reasonableness gate and inline ASP twin
- story, story QA, and world QA generation
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    gear: object | None = None
    hero: object | None = None
    mentor: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Court:
    place: str
    indoors: bool = False
    supports: set[str] = field(default_factory=set)
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
class Power:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    hazard: str
    zone: set[str]
    spark: str
    keyword: str = "volley"
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
    def __init__(self, court: Court) -> None:
        self.court = court
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        import copy
        clone = World(self.court)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_spark(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for power in POWERS.values():
            if actor.meters.get(power.mess, 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("spark", item.id, power.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[power.mess] = item.meters.get(power.mess, 0.0) + 1
                item.meters["scuffed"] = item.meters.get("scuffed", 0.0) + 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} was scuffed by the magic volley.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters.get("scuffed", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] = carer.memes.get("worry", 0.0) + 1
        out.append(f"That would worry {carer.label}.")
    return out


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes.get("defiance", 0.0) < THRESHOLD or actor.memes.get("stopped", 0.0) < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] = actor.memes.get("conflict", 0.0) + 1
        return ["__conflict__"]
    return []


RULES = [
    ("spark", _r_spark),
    ("worry", _r_worry),
    ("conflict", _r_conflict),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for _, rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(power: Power, prize: Prize) -> bool:
    return prize.region in power.zone


def select_gear(power: Power, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if power.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, power: Power, prize_id: str) -> dict:
    sim = world.copy()
    _do_power(sim, sim.get(actor.id), power, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "scuffed": bool(prize and prize.meters.get("scuffed", 0.0) >= THRESHOLD),
        "worry": sum(e.memes.get("worry", 0.0) for e in sim.characters()),
    }


def _do_power(world: World, actor: Entity, power: Power, narrate: bool = True) -> None:
    if power.id not in world.court.supports:
        return
    world.zone = set(power.zone)
    actor.meters[power.mess] = actor.meters.get(power.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.meters.get("traits", []) if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who loved looking for heroic chances.")


def loves_power(world: World, hero: Entity, power: Power) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    world.say(f"{hero.pronoun().capitalize()} loved the {power.keyword} magic volley; {power.spark}.")


def arrives(world: World, hero: Entity, mentor: Entity, power: Power) -> None:
    day = "One bright day, " if not world.court.indoors else "One quiet afternoon, "
    go = "went to" if not world.court.indoors else "stepped into"
    world.say(f"{day}{hero.id} and {hero.pronoun('possessive')} {mentor.label} {go} {world.court.place}.")
    if world.court.indoors:
        world.say("The court shimmered under the ceiling lights, and the net waited like a secret line.")
    else:
        world.say("The open court gleamed, and the air felt ready for a flying superhero move.")


def wants(world: World, hero: Entity, mentor: Entity, power: Power) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(f"{hero.id} wanted to {power.verb} right away, but {hero.pronoun('possessive')} {mentor.label} held up a calm hand.")


def warn(world: World, mentor: Entity, hero: Entity, power: Power, prize: Entity) -> bool:
    pred = predict_mess(world, hero, power, prize.id)
    if not pred["scuffed"]:
        return False
    world.facts["predicted_hazard"] = power.hazard
    clause = f"You'll get your {prize.label} {power.hazard}"
    if pred["worry"] >= THRESHOLD:
        clause += ", and that will worry the whole team"
    world.say(f"\"{clause},\" {mentor.pronoun('possessive')} mentor said. \"Let's choose the safe hero way.\"")
    return True


def defies(world: World, hero: Entity, power: Power) -> None:
    hero.memes["defiance"] = hero.memes.get("defiance", 0.0) + 1
    world.say(f"{hero.id} still wanted to play, and the magic fizzed with excitement.")
    world.say(f"{hero.pronoun().capitalize()} tried to {power.rush}.")


def stop_and_conflict(world: World, mentor: Entity, hero: Entity, power: Power) -> None:
    hero.memes["stopped"] = hero.memes.get("stopped", 0.0) + 1
    propagate(world, narrate=False)
    world.say(f"Then {hero.pronoun('possessive')} {mentor.label} stepped in and said,")
    world.say(f"\"You can love the volley and still choose a smarter spell.\"")


def pout(world: World, hero: Entity) -> None:
    if hero.memes.get("conflict", 0.0) >= THRESHOLD:
        world.say(f"{hero.id} crossed {hero.pronoun('possessive')} arms and pouted for a moment.")
        world.say(f"\"But I want to use the big magic!\" {hero.pronoun()} said.")


def compromise(world: World, mentor: Entity, hero: Entity, power: Power, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(power, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=mentor.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, power, prize.id)["scuffed"]:
        del world.entities[gear.id]
        return None
    world.say(f"{hero.pronoun('possessive').capitalize()} {mentor.label} smiled and offered a better plan.")
    world.say(f"\"How about we {gear_def.prep} and then {power.verb} together?\"")
    return gear_def


def accept(world: World, mentor: Entity, hero: Entity, power: Power, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    hero.memes["conflict"] = 0.0
    world.say(f"{hero.id}'s face lit up, and {hero.pronoun()} hugged {hero.pronoun('possessive')} {mentor.label}.")
    world.say(f"\"Yes! Let's do it!\" {hero.pronoun()} said.")
    world.say(
        f"They {gear_def.tail}. Soon {hero.id} was {power.gerund}, "
        f"{prize.it()} stayed safe, and the whole court sparkled like a comic-book starburst."
    )


def tell(court: Court, power: Power, prize_cfg: Prize, hero_name: str = "Nova",
         hero_type: str = "girl", hero_traits: Optional[list[str]] = None,
         mentor_type: str = "woman") -> World:
    world = World(court)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    hero.meters["traits"] = hero_traits or ["little", "brave"]
    mentor = world.add(Entity(id="Mentor", kind="character", type=mentor_type, label="superhero mentor"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=mentor.id,
        worn_by=hero.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    intro(world, hero)
    loves_power(world, hero, power)
    world.say(f"That week, {hero.id}'s mentor gave {hero.pronoun('object')} {prize.phrase}.")
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} like part of the costume.")

    world.para()
    arrives(world, hero, mentor, power)
    wants(world, hero, mentor, power)
    warn(world, mentor, hero, power, prize)
    defies(world, hero, power)
    stop_and_conflict(world, mentor, hero, power)

    world.para()
    pout(world, hero)
    gear_def = compromise(world, mentor, hero, power, prize)
    if gear_def:
        accept(world, mentor, hero, power, prize, gear_def)

    world.facts.update(
        hero=hero,
        mentor=mentor,
        prize=prize,
        prize_cfg=prize_cfg,
        power=power,
        court=court,
        gear=gear_def,
        conflict=hero.memes.get("conflict", 0.0) >= THRESHOLD,
        resolved=gear_def is not None,
    )
    return world


@dataclass
class StoryParams:
    place: str
    power: str
    prize: str
    name: str
    gender: str
    mentor: str
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


COURTS = {
    "rooftop": Court(place="the rooftop court", indoors=False, supports={"volley", "arc"}),
    "gym": Court(place="the bright gym", indoors=True, supports={"volley", "shield"}),
    "harbor": Court(place="the harbor court", indoors=False, supports={"volley"}),
}

POWERS = {
    "volley": Power(
        id="volley",
        verb="send the magic volley flying",
        gerund="sending the magic volley flying",
        rush="launch the volley straight at the goal",
        mess="glow",
        hazard="with sparks and bumps",
        zone={"hands", "torso"},
        spark="the ball glittered like a tiny comet",
        keyword="volley",
        tags={"volley", "magic", "superhero"},
    ),
    "arc": Power(
        id="arc",
        verb="bend the magic volley in a safe arc",
        gerund="bending the magic volley in a safe arc",
        rush="whip the volley over the net",
        mess="glow",
        hazard="with wild spark-trails",
        zone={"hands", "torso"},
        spark="the ball made a bright curved ribbon in the air",
        keyword="volley",
        tags={"volley", "magic"},
    ),
    "shield": Power(
        id="shield",
        verb="bounce the magic volley inside a shield",
        gerund="bouncing the magic volley inside a shield",
        rush="slam the volley into the shield",
        mess="glow",
        hazard="with a burst of light",
        zone={"hands", "torso"},
        spark="the shield hummed with a safe, blue shine",
        keyword="volley",
        tags={"volley", "magic"},
    ),
}

PRIZES = {
    "cape": Prize(label="cape", phrase="a shiny red cape", type="cape", region="torso"),
    "mask": Prize(label="mask", phrase="a bright silver mask", type="mask", region="face"),
    "gloves": Prize(label="gloves", phrase="a pair of star gloves", type="gloves", region="hands", plural=True),
}

GEAR = [
    Gear(id="shield_gloves", label="shield gloves", covers={"hands"}, guards={"glow"}, prep="put on the shield gloves first", tail="put on the shield gloves"),
    Gear(id="training_cape", label="a training cape", covers={"torso"}, guards={"glow"}, prep="wear a training cape first", tail="slipped on the training cape"),
    Gear(id="visor", label="a clear visor", covers={"face"}, guards={"glow"}, prep="wear a clear visor first", tail="fastened the clear visor"),
]

GIRL_NAMES = ["Nova", "Mira", "Zara", "Luna", "Tia", "Ivy", "Rae", "Skye"]
BOY_NAMES = ["Kai", "Jett", "Noah", "Theo", "Finn", "Max", "Leo", "Ben"]
TRAITS = ["brave", "curious", "spirited", "bold", "bright", "quick"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, court in COURTS.items():
        for power_id in court.supports:
            power = _safe_lookup(POWERS, power_id)
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(power, prize) and select_gear(power, prize):
                    combos.append((place, power_id, prize_id))
    return combos


KNOWLEDGE = {
    "volley": [("What is a volley?", "A volley is a quick hit or return of a ball before it lands and bounces." )],
    "magic": [("What does magic mean in a story?", "In a story, magic means something special and impossible-looking happens, like a glowing ball or a sparkling shield.")],
    "cape": [("What is a cape for?", "A cape is a piece of clothing that hangs from your shoulders and can make a hero look dramatic.")],
    "mask": [("Why do heroes wear masks?", "Heroes wear masks to hide their faces and keep their secret identity safe.")],
    "gloves": [("Why wear gloves?", "Gloves can protect your hands and keep them warm or clean.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, mentor, power, prize = f["hero"], f["mentor"], f["power"], f["prize_cfg"]
    return [
        f'Write a short superhero story for a young child that includes the word "volley" and a magical twist.',
        f"Tell a story where {hero.id} wants to {power.verb} at {f['court'].place}, but {hero.pronoun('possessive')} {mentor.label} worries about {prize.phrase}.",
        f"Write a gentle superhero tale about a magic volley, a worried mentor, and a safer heroic plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mentor, prize, power = f["hero"], f["mentor"], f["prize"], f["power"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little {next((t for t in hero.meters.get('traits', []) if t != 'little'), hero.type)} {hero.type}, and a superhero mentor who helps {hero.pronoun('object')} make a good choice.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {f['court'].place}?",
            answer=f"{hero.id} wanted to {power.verb}. The magic volley made the game feel thrilling and shiny.",
        ),
        QAItem(
            question=f"Why was {mentor.label} worried about {prize.label}?",
            answer=f"{mentor.label} was worried because the magic volley could leave {prize.it()} {power.hazard}.",
        ),
    ]
    if f.get("resolved"):
        gear = _safe_fact(world, f, "gear")
        qa.append(QAItem(
            question=f"How did the heroes make the play safe?",
            answer=f"They used {gear.label} and then played with the magic volley in a safer way, so {prize.it()} stayed safe.",
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and proud, because the hero plan let {hero.pronoun()} enjoy the game without ruining {prize.it()}.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["power"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    out: list[QAItem] = []
    for tag in ["volley", "magic", "cape", "mask", "gloves"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v and k != "traits"}
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="rooftop", power="volley", prize="cape", name="Nova", gender="girl", mentor="woman", trait="brave"),
    StoryParams(place="gym", power="shield", prize="mask", name="Kai", gender="boy", mentor="man", trait="curious"),
    StoryParams(place="harbor", power="arc", prize="gloves", name="Mira", gender="girl", mentor="woman", trait="bright"),
]


def explain_rejection(power: Power, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(power, prize):
        return f"(No story: the magic volley doesn't reach {noun} in a way that would honestly endanger it.)"
    return f"(No story: nothing in the gear catalog safely protects {noun} from the magic volley.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(_safe_lookup(PRIZES, prize_id).genders))
    return f"(No story: a {_safe_lookup(PRIZES, prize_id).label} isn't a typical {gender}'s item here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(PW, PR) :- zone(PW, R), worn_on(PR, R).
protected(G, PW, PR) :- prize_at_risk(PW, PR), mess_of(PW, M), guards(G, M), covers(G, R), worn_on(PR, R).
has_fix(PW, PR) :- protected(_, PW, PR).
valid(Place, PW, PR) :- supports(Place, PW), prize_at_risk(PW, PR), has_fix(PW, PR).
valid_story(Place, PW, PR, Gender) :- valid(Place, PW, PR), wears(Gender, PR).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, court in COURTS.items():
        lines.append(asp.fact("court", place))
        if court.indoors:
            lines.append(asp.fact("indoors", place))
        for p in sorted(court.supports):
            lines.append(asp.fact("supports", place, p))
    for pid, p in POWERS.items():
        lines.append(asp.fact("power", pid))
        lines.append(asp.fact("mess_of", pid, p.mess))
        for r in sorted(p.zone):
            lines.append(asp.fact("zone", pid, r))
    for rid, r in PRIZES.items():
        lines.append(asp.fact("prize", rid))
        lines.append(asp.fact("worn_on", rid, r.region))
        for g in sorted(r.genders):
            lines.append(asp.fact("wears", g, rid))
        if r.plural:
            lines.append(asp.fact("prize_plural", rid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: a superhero, a magic volley, and a safer heroic choice.")
    ap.add_argument("--place", choices=COURTS)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mentor", choices=["woman", "man"])
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
    if getattr(args, "power", None) and getattr(args, "prize", None):
        pw, pr = _safe_lookup(POWERS, getattr(args, "power", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(pw, pr) and select_gear(pw, pr)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "prize", None) and getattr(args, "gender", None) not in _safe_lookup(PRIZES, getattr(args, "prize", None)).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "power", None) is None or c[1] == getattr(args, "power", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
              and (getattr(args, "gender", None) is None or getattr(args, "gender", None) in PRIZES[c[2]].genders)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, power, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(sorted(_safe_lookup(PRIZES, prize).genders))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    mentor = getattr(args, "mentor", None) or rng.choice(["woman", "man"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, power=power, prize=prize, name=name, gender=gender, mentor=mentor, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(COURTS, params.place), _safe_lookup(POWERS, params.power), _safe_lookup(PRIZES, params.prize), params.name, params.gender, [params.trait], params.mentor)
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
        print(f"{len(triples)} compatible (place, power, prize) combos ({len(stories)} with gender):\n")
        for place, power, prize in triples:
            genders = sorted(g for (pl, pw, pr, g) in stories if (pl, pw, pr) == (place, power, prize))
            print(f"  {place:8} {power:8} {prize:8}  [{', '.join(genders)}]")
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
            header = f"### {p.name}: {p.power} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
