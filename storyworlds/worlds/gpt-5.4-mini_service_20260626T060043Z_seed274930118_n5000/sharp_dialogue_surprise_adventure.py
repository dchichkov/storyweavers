#!/usr/bin/env python3
"""
storyworlds/worlds/sharp_dialogue_surprise_adventure.py
========================================================

A small adventure storyworld about a child on a tiny expedition, a sharp
problem, and a surprise solution reached through dialogue.

Premise:
- A young adventurer wants to explore a new place.
- Something sharp blocks the path or threatens a treasured item.
- The guide/companion warns them, and they talk through a safer choice.
- The story ends with a concrete adventure image that proves the change.

This world keeps the prose close to Adventure:
- outdoor, concrete settings
- a simple goal
- a surprising obstacle
- dialogue used as the turning point
- a satisfying, image-rich ending

The world model tracks both physical meters and emotional memes so the story is
driven by state rather than a frozen paragraph.
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
    carried_by: Optional[str] = None
    protective: bool = False
    sharp: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    g: object | None = None
    guide: object | None = None
    hero: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        for k in ["danger", "scrape", "dust", "joy", "curiosity", "fear", "surprise", "trust", "conflict"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister", "aunt"}
        male = {"boy", "father", "man", "brother", "uncle"}
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
    place: str
    affords: set[str] = field(default_factory=set)
    mood: str = "bright"
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
    goal: str
    approach: str
    surprise: str
    danger: str
    result: str
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
class Item:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
    answer: object | None = None
    question: object | None = None
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
    offer: str
    ending: str
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
        self.fired: set[tuple] = set()
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

    def carried_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.facts = dict(self.facts)
        return clone


def _r_sharp(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["danger"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or not item.sharp:
                continue
            sig = ("sharp", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["scrape"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} caught on something sharp.")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["surprise"] < THRESHOLD:
            continue
        sig = ("surprise", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["trust"] += 1
        out.append(f"The surprise made {actor.id} stop and listen.")
    return out


CAUSAL_RULES = [
    ("sharp", _r_sharp),
    ("surprise", _r_surprise),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for _, rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_challenge(world: World, actor: Entity, challenge: Challenge, narrate: bool = True) -> None:
    if challenge.id not in world.setting.affords:
        pass
    world.zone = set(challenge.zone)
    actor.meters["danger"] += 1
    actor.memes["curiosity"] += 1
    actor.memes["surprise"] += 1
    propagate(world, narrate=narrate)


def predict_outcome(world: World, actor: Entity, challenge: Challenge, prize_id: str) -> dict:
    sim = world.copy()
    _do_challenge(sim, sim.get(actor.id), challenge, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "scraped": bool(prize and prize.meters["scrape"] >= THRESHOLD),
        "trust": sum(e.memes["trust"] for e in sim.characters()),
    }


def setting_detail(setting: Setting, challenge: Challenge) -> str:
    if "cave" in setting.place:
        return "The cave mouth was cool and dim, with pebbles clicking under small boots."
    if "trail" in setting.place:
        return "The trail curved through bright grass and leaned into the trees."
    if "river" in setting.place:
        return "The river flashed silver, and the bank was lined with smooth stones."
    if "tower" in setting.place:
        return "The old tower stood high, with windy steps and a door that looked too small."
    return f"{setting.place.capitalize()} felt ready for an adventure."


def hero_intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "brave")
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved small adventures.")


def loves_goal(world: World, hero: Entity, challenge: Challenge) -> None:
    hero.memes["joy"] += 1
    world.say(f"{hero.pronoun().capitalize()} loved to {challenge.goal} and see what was waiting ahead.")


def carries_item(world: World, hero: Entity, item: Entity) -> None:
    item.carried_by = hero.id
    hero.memes["joy"] += 0.5
    world.say(f"{hero.id} carried {hero.pronoun('possessive')} {item.label} carefully like a treasure.")


def arrives(world: World, hero: Entity, guide: Entity, challenge: Challenge) -> None:
    world.say(f"One day, {hero.id} and {guide.label} went to {world.setting.place}.")
    world.say(setting_detail(world.setting, challenge))


def wants(world: World, hero: Entity, challenge: Challenge) -> None:
    world.say(f"{hero.id} wanted to {challenge.goal} right away.")
    world.say(f'"{challenge.approach}," {hero.id} said, leaning forward with excitement.')


def warn(world: World, guide: Entity, hero: Entity, challenge: Challenge, item: Entity) -> bool:
    pred = predict_outcome(world, hero, challenge, item.id)
    if not pred["scraped"]:
        return False
    world.facts["predicted_result"] = challenge.result
    world.facts["predicted_trust"] = pred["trust"]
    world.say(
        f'"Careful," {guide.label} said. "That path could leave your {item.label} {challenge.result}."'
    )
    return True


def reacts(world: World, hero: Entity, challenge: Challenge) -> None:
    hero.memes["conflict"] += 1
    world.say(f"{hero.id} frowned, because the adventure looked too tempting to stop.")
    world.say(f"{hero.id} tried to {challenge.surprise}.")


def dialogue_turn(world: World, guide: Entity, hero: Entity, item: Entity, challenge: Challenge) -> None:
    hero.memes["surprise"] += 1
    hero.memes["trust"] += 1
    world.say(
        f'"What if we take the side steps instead?" {guide.label} asked. '
        f'"Then the sharp part stays away from your {item.label}."'
    )
    world.say(f'"Oh!" {hero.id} said. "That is a better way."')


def accept(world: World, hero: Entity, guide: Entity, item: Entity, challenge: Challenge, gear: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["trust"] += 1
    hero.memes["conflict"] = 0.0
    if gear.id not in world.entities:
        g = world.add(Entity(id=gear.id, type="gear", label=gear.label, protective=True, plural=gear.plural))
        g.worn_by = hero.id
    world.say(
        f'{hero.id} put on {gear.label} first, and they {gear.ending}. '
        f'Soon {hero.id} was {challenge.approach}, and the sharp trouble was safely behind them.'
    )


def tell(setting: Setting, challenge: Challenge, prize_cfg: Item,
         hero_name: str = "Maya", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, guide_type: str = "father") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["curious", "brave"])))
    guide = world.add(Entity(id="Guide", kind="character", type=guide_type, label="the guide"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
                             region=prize_cfg.region, owner=hero.id, caretaker=guide.id, plural=prize_cfg.plural))
    hero_intro(world, hero)
    loves_goal(world, hero, challenge)
    carries_item(world, hero, prize)
    world.para()
    arrives(world, hero, guide, challenge)
    wants(world, hero, challenge)
    warn(world, guide, hero, challenge, prize)
    reacts(world, hero, challenge)
    dialogue_turn(world, guide, hero, prize, challenge)
    world.para()
    gear = select_gear(challenge, prize)
    if gear:
        accept(world, hero, guide, prize, challenge, gear)
    world.facts.update(hero=hero, guide=guide, prize=prize, challenge=challenge, gear=gear, resolved=bool(gear))
    return world


SETTINGS = {
    "trail": Setting(place="the forest trail", affords={"ridge", "crossing", "trail"},
                     mood="bright"),
    "cave": Setting(place="the cave mouth", affords={"cave", "crossing"}, mood="dim"),
    "river": Setting(place="the riverbank path", affords={"river", "crossing"}, mood="windy"),
    "tower": Setting(place="the old tower stairs", affords={"tower", "crossing"}, mood="echoing"),
}

CHALLENGES = {
    "ridge": Challenge(
        id="ridge",
        goal="cross the ridge",
        approach="walk across the ridge",
        surprise="notice the hidden step",
        danger="sharp",
        result="scratched",
        zone={"feet", "legs"},
        keyword="ridge",
        tags={"sharp", "adventure"},
    ),
    "cave": Challenge(
        id="cave",
        goal="enter the cave",
        approach="step into the cave",
        surprise="peek behind the rock",
        danger="sharp",
        result="scraped",
        zone={"feet", "hands"},
        keyword="cave",
        tags={"sharp", "surprise"},
    ),
    "crossing": Challenge(
        id="crossing",
        goal="cross the stepping stones",
        approach="jump from stone to stone",
        surprise="look under the bridge",
        danger="sharp",
        result="torn",
        zone={"feet"},
        keyword="stones",
        tags={"sharp", "adventure"},
    ),
    "tower": Challenge(
        id="tower",
        goal="climb the tower stairs",
        approach="climb the tower stairs",
        surprise="open the tiny door",
        danger="sharp",
        result="scuffed",
        zone={"feet", "hands"},
        keyword="tower",
        tags={"surprise", "adventure"},
    ),
}

PRIZES = {
    "boots": Item(label="boots", phrase="sturdy adventure boots", type="boots", region="feet", plural=True),
    "cloak": Item(label="cloak", phrase="a bright trail cloak", type="cloak", region="torso"),
    "gloves": Item(label="gloves", phrase="soft climbing gloves", type="gloves", region="hands", plural=True),
    "satchel": Item(label="satchel", phrase="a small explorer's satchel", type="satchel", region="torso"),
}

GEAR = [
    Gear(id="thickboots", label="thick boots", covers={"feet"}, guards={"sharp"}, offer="put on thick boots first", ending="followed the safer stones", plural=True),
    Gear(id="gloves", label="padded gloves", covers={"hands"}, guards={"sharp"}, offer="wear padded gloves first", ending="climbed with careful hands", plural=True),
    Gear(id="cloak", label="a tough cloak", covers={"torso"}, guards={"sharp"}, offer="wear the tough cloak first", ending="moved along the path with one safe step after another"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for ch_id in setting.affords:
            ch = _safe_lookup(CHALLENGES, ch_id)
            for prize_id, prize in PRIZES.items():
                if prize.region in ch.zone:
                    for gear in GEAR:
                        if prize.region in gear.covers and "sharp" in gear.guards:
                            combos.append((place, ch_id, prize_id))
                            break
    return combos


@dataclass
class StoryParams:
    place: str
    challenge: str
    prize: str
    name: str
    gender: str
    guide: str
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


KNOWLEDGE = {
    "sharp": [
        ("What does sharp mean?", "Sharp means having a point or edge that can cut, scratch, or poke."),
    ],
    "boots": [
        ("What are boots for?", "Boots protect your feet and help you walk on rough ground."),
    ],
    "gloves": [
        ("Why wear gloves?", "Gloves help protect your hands and keep them warm or safe while you work."),
    ],
    "cave": [
        ("What is a cave?", "A cave is a hollow space in rock or a hill where animals or people can shelter."),
    ],
    "river": [
        ("What is a riverbank?", "A riverbank is the land right next to a river."),
    ],
    "tower": [
        ("What is a tower?", "A tower is a tall building or structure that rises high above the ground."),
    ],
    "surprise": [
        ("What is a surprise?", "A surprise is something you did not expect to happen."),
    ],
    "adventure": [
        ("What is an adventure?", "An adventure is an exciting trip or experience with new things to discover."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, guide, ch, prize = f["hero"], f["guide"], f["challenge"], f["prize"]
    return [
        f'Write a short adventure story for a child about "{ch.keyword}" and a sharp surprise.',
        f"Tell a story where {hero.id} wants to {ch.goal} but {guide.label} worries about {prize.label}.",
        f'Write a simple adventure with dialogue that ends after a safer choice is made around something sharp.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, guide, ch, prize = f["hero"], f["guide"], f["challenge"], f["prize"]
    qa = [
        QAItem(
            question=f"Who wanted to {ch.goal} in the story?",
            answer=f"{hero.id} wanted to {ch.goal}, while {guide.label} watched carefully.",
        ),
        QAItem(
            question=f"What was the sharp problem in the adventure?",
            answer=f"The sharp problem was that the path could leave {hero.id}'s {prize.label} {ch.result}.",
        ),
        QAItem(
            question=f"How did the dialogue help?",
            answer=f"{guide.label} suggested a safer way, and {hero.id} listened instead of rushing ahead.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"What happened after they chose the safer way?",
                answer=f"They kept going on the adventure, and {hero.id} could still {ch.approach} without danger."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["challenge"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    out: list[QAItem] = []
    for key, items in KNOWLEDGE.items():
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
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
    lines.append("== (3) World knowledge ==")
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
            bits.append("protective=True")
        if e.sharp:
            bits.append("sharp=True")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="trail", challenge="ridge", prize="boots", name="Ava", gender="girl", guide="father", trait="brave"),
    StoryParams(place="cave", challenge="cave", prize="gloves", name="Finn", gender="boy", guide="mother", trait="curious"),
    StoryParams(place="river", challenge="crossing", prize="boots", name="Mia", gender="girl", guide="father", trait="lively"),
    StoryParams(place="tower", challenge="tower", prize="cloak", name="Theo", gender="boy", guide="mother", trait="cheerful"),
]


def explain_rejection(ch: Challenge, prize: Item) -> str:
    return f"(No story: {ch.goal} does not honestly threaten the {prize.label}, so there is no sharp problem to solve.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(_safe_lookup(PRIZES, prize_id).genders))
    return f"(No story: {_safe_lookup(PRIZES, prize_id).label} is not a typical {gender}'s item here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(C, P) :- sharp_zone(C, R), worn_on(P, R).
compatible(C, P) :- prize_at_risk(C, P), gear_fix(P, R), sharp_zone(C, R).
valid(Place, C, P) :- affords(Place, C), compatible(C, P).
valid_story(Place, C, P, Gender) :- valid(Place, C, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for ch in sorted(s.affords):
            lines.append(asp.fact("affords", pid, ch))
    for cid, ch in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        for r in sorted(ch.zone):
            lines.append(asp.fact("sharp_zone", cid, r))
    for iid, item in PRIZES.items():
        lines.append(asp.fact("prize", iid))
        lines.append(asp.fact("worn_on", iid, item.region))
        if item.plural:
            lines.append(asp.fact("prize_plural", iid))
        for g in sorted(item.genders):
            lines.append(asp.fact("wears", g, iid))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for r in sorted(gear.covers):
            lines.append(asp.fact("gear_fix", gear.id, r))
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
    ap = argparse.ArgumentParser(description="Adventure story world with sharp surprise and dialogue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide", choices=["mother", "father"])
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
    if getattr(args, "challenge", None) and getattr(args, "prize", None):
        ch, pr = _safe_lookup(CHALLENGES, getattr(args, "challenge", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (pr.region in ch.zone):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "prize", None) and getattr(args, "gender", None) not in _safe_lookup(PRIZES, getattr(args, "prize", None)).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "challenge", None) is None or c[1] == getattr(args, "challenge", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
              and (getattr(args, "gender", None) is None or getattr(args, "gender", None) in PRIZES[c[2]].genders)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, challenge, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(sorted(_safe_lookup(PRIZES, prize).genders))
    name = getattr(args, "name", None) or rng.choice(["Ava", "Mia", "Lina", "Nora", "Finn", "Theo", "Eli", "Noah"])
    guide = getattr(args, "guide", None) or rng.choice(["mother", "father"])
    trait = rng.choice(["curious", "brave", "lively", "cheerful", "stubborn"])
    return StoryParams(place=place, challenge=challenge, prize=prize, name=name, gender=gender, guide=guide, trait=trait)


def select_gear(challenge: Challenge, prize: Item) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and "sharp" in gear.guards:
            return gear
    return None


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(CHALLENGES, params.challenge), _safe_lookup(PRIZES, params.prize),
                 params.name, params.gender, [params.trait, "stubborn"], params.guide)
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
        print(f"{len(triples)} compatible (place, challenge, prize) combos ({len(stories)} with gender):\n")
        for place, ch, prize in triples:
            genders = sorted(g for (pl, c, pr, g) in stories if (pl, c, pr) == (place, ch, prize))
            print(f"  {place:8} {ch:10} {prize:8} [{', '.join(genders)}]")
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
            header = f"### {p.name}: {p.challenge} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
