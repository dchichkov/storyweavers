#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/exert_sound_effects_cautionary_lesson_learned_ghost.py
=====================================================================================================

A small ghost-story world about a young ghost who wants to exert itself
making spooky sound effects, learns a cautionary lesson, and ends with a
gentle, child-facing resolution.

The story premise is simple: a ghost wants to be loud and impressive, but the
best lesson learned is that sound effects are most fun when they stay safe,
small, and kind.
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
RISKY = {"rustle", "clang", "howl", "creak"}
QUIET = {"tap", "whisper", "hum"}



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
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    g: object | None = None
    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    def __post_init__(self):
        self.meters = __import__('collections').defaultdict(float, self.meters)
        self.memes = __import__('collections').defaultdict(float, self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
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
    mood: str
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    sound: str
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.zone = set(self.zone)
        c.facts = dict(self.facts)
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in RISKY:
            if actor.meters.get(mess, 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone or world.covered(actor, item.region):
                    continue
                sig = ("noise", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] = item.meters.get(mess, 0.0) + 1
                item.meters["frightened"] = item.meters.get("frightened", 0.0) + 1
                out.append(f"The sound shook {item.label}.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters.get("frightened", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] = carer.memes.get("worry", 0.0) + 1
        out.append("That would worry the grown-up nearby.")
    return out


CAUSAL_RULES = [
    ("noise", _r_noise),
    ("worry", _r_worry),
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


def activity_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"frightened": prize.meters.get("frightened", 0.0) >= THRESHOLD,
            "worry": sum(e.memes.get("worry", 0.0) for e in sim.characters())}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        pass
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["exert"] = actor.memes.get("exert", 0.0) + 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little ghost who liked the dark corners of {world.setting.place}.")


def love_sound_effects(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f"{hero.pronoun().capitalize()} loved making sound effects and trying to {activity.verb}.")


def bring_prize(world: World, hero: Entity, prize: Entity, parent: Entity) -> None:
    world.say(f"{hero.id} had {hero.pronoun('possessive')} {prize.label}, and {parent.label} had given it to {hero.pronoun('object')} carefully.")
    prize.worn_by = hero.id


def arrive(world: World, hero: Entity) -> None:
    world.say(f"One moonlit night, {hero.id} drifted into {world.setting.place}.")


def wants(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f"{hero.id} wanted to {activity.verb} and really exert {hero.pronoun('possessive')} spooky voice.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["frightened"]:
        return False
    world.facts["predicted_worry"] = pred["worry"]
    world.say(f'"If you go too far, your {prize.label} will get {activity.soil}," {parent.pronoun("possessive")} voice said. "A ghost should be careful."')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f"But {hero.id} still tried to {activity.rush}.")
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 1


def caution(world: World, hero: Entity) -> None:
    if hero.memes.get("stubborn", 0.0) >= THRESHOLD:
        world.say(f"The old floorboards gave a soft creak, and even the candles seemed to listen.")


def offer(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    g = world.add(Entity(id=gear.id, type="gear", label=gear.label, protective=True, covers=set(gear.covers), plural=gear.plural))
    g.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["frightened"]:
        del world.entities[g.id]
        return None
    world.say(f'{parent.id} held up a gentle hand and said, "How about we {gear.prep} instead?"')
    return gear


def accept(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["worry"] = 0.0
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    world.say(f"{hero.id} nodded, floated closer, and put on {gear.label}.")
    world.say(f"They {gear.tail}. Then {hero.id} could {activity.gerund} in a quiet way, and {prize.label} stayed safe.")
    world.say("It was a small lesson learned: a ghost did not need to be the loudest thing in the room.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Boo", hero_type: str = "ghost", parent_type: str = "grandmother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Grandmother", kind="character", type=parent_type, label="Grandmother"))
    prize = world.add(Entity(id="prize", label=prize_cfg.label, phrase=prize_cfg.phrase, region=prize_cfg.region, plural=prize_cfg.plural, owner=hero.id, caretaker=parent.id))
    intro(world, hero)
    love_sound_effects(world, hero, activity)
    bring_prize(world, hero, prize, parent)
    world.para()
    arrive(world, hero)
    wants(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    caution(world, hero)
    gear = offer(world, parent, hero, activity, prize)
    world.para()
    if gear:
        accept(world, hero, parent, activity, prize, gear)
    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting, gear=gear)
    return world


SETTINGS = {
    "attic": Setting(place="the attic", mood="dusty", affords={"howl", "clang"}),
    "hallway": Setting(place="the hallway", mood="quiet", affords={"creak", "whisper"}),
    "garden": Setting(place="the moonlit garden", mood="misty", affords={"rustle", "tap"}),
}

ACTIVITIES = {
    "howl": Activity(
        id="howl",
        verb="howl at the moon",
        gerund="howling softly",
        rush="rush down the hallway howling",
        sound="howl",
        mess="noise",
        soil="loud and shaky",
        zone={"torso"},
        keyword="howl",
        tags={"ghost", "sound"},
    ),
    "clang": Activity(
        id="clang",
        verb="clang the old bell",
        gerund="clanging the bell",
        rush="bang the bell again and again",
        sound="clang",
        mess="noise",
        soil="loud and rattly",
        zone={"torso", "hands"},
        keyword="clang",
        tags={"ghost", "sound"},
    ),
    "rustle": Activity(
        id="rustle",
        verb="rustle the curtains",
        gerund="rustling the curtains",
        rush="whip through the curtains",
        sound="rustle",
        mess="noise",
        soil="creepy and loud",
        zone={"torso"},
        keyword="rustle",
        tags={"ghost", "sound"},
    ),
    "creak": Activity(
        id="creak",
        verb="creak the floorboards",
        gerund="creaking the floorboards",
        rush="stomp around to make the boards squeal",
        sound="creak",
        mess="noise",
        soil="scary and noisy",
        zone={"feet", "torso"},
        keyword="creak",
        tags={"ghost", "sound"},
    ),
    "whisper": Activity(
        id="whisper",
        verb="whisper a spooky rhyme",
        gerund="whispering a rhyme",
        rush="hiss the rhyme too hard",
        sound="whisper",
        mess="noise",
        soil="thin and eerie",
        zone={"mouth"},
        keyword="whisper",
        tags={"ghost", "sound"},
    ),
}

PRIZES = {
    "lantern": Prize(label="lantern", phrase="a small lantern", region="hands"),
    "ribbon": Prize(label="ribbon", phrase="a silver ribbon", region="torso"),
    "bell": Prize(label="bell", phrase="a tiny bell", region="hands"),
}

GEAR = [
    Gear(
        id="softvoice",
        label="a soft-voice scarf",
        covers={"mouth", "torso"},
        guards={"noise"},
        prep="tie on a soft-voice scarf first",
        tail="floated back and tied on the soft-voice scarf",
    ),
    Gear(
        id="gloves",
        label="a pair of mitten-gloves",
        covers={"hands"},
        guards={"noise"},
        prep="put on a pair of mitten-gloves first",
        tail="slid into the mitten-gloves",
        plural=True,
    ),
    Gear(
        id="slippers",
        label="quiet slippers",
        covers={"feet"},
        guards={"noise"},
        prep="wear quiet slippers first",
        tail="put on the quiet slippers",
        plural=True,
    ),
]

CURATED = [
    ("attic", "clang", "bell"),
    ("hallway", "creak", "lantern"),
    ("garden", "rustle", "ribbon"),
]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str = "Boo"
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost story for a child about "{f["activity"].keyword}" and a cautionary lesson learned.',
        f"Tell a gentle spooky tale where {f['hero'].id} wants to {f['activity'].verb} but must be careful with {f['prize'].label}.",
        f'Write a story that includes a child-friendly sound effect like "{f["activity"].sound}" and ends with a safer choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do in {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb}, because {hero.pronoun().capitalize()} liked spooky sound effects.",
        ),
        QAItem(
            question=f"Why did {parent.label} warn {hero.id}?",
            answer=f"{parent.label} warned {hero.id} because too much {act.sound} would make the {prize.label} get {act.soil}.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer="The lesson learned was that a ghost can be spooky without being loud and unsafe.",
        ),
    ]
    if f.get("gear"):
        gear = _safe_fact(world, f, "gear")
        qa.append(QAItem(
            question=f"How did {gear.label} help?",
            answer=f"{gear.label} helped {hero.id} make the sound in a gentler way so the {prize.label} stayed safe.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a ghost story?", answer="A ghost story is a spooky tale about a ghost or other eerie thing, usually told in a gentle way for children."),
        QAItem(question="What do sound effects do in a story?", answer="Sound effects help the story feel alive by suggesting noises like whispers, creaks, or clangs."),
        QAItem(question="What does cautionary mean?", answer="Cautionary means a story gives a warning or lesson so someone can avoid trouble."),
        QAItem(question="What is a lesson learned?", answer="A lesson learned is something a character understands after making a mistake or seeing what happens."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


ASP_RULES = r"""
risk(A,P) :- splashes(A,R), worn_on(P,R).
fix(G,A,P) :- risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R), splashes(A,R).
valid(Place,A,P) :- affords(Place,A), risk(A,P), fix(_,A,P).
#show valid/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, s in SETTINGS.items():
        for aid in s.affords:
            a = _safe_lookup(ACTIVITIES, aid)
            for pid, p in PRIZES.items():
                if activity_risk(a, p) and select_gear(a, p):
                    out.append((place, aid, pid))
    return sorted(out)


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} valid combos.")
        return 0
    print("MISMATCH:")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world about sound effects, caution, and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
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
    combos = valid_combos()
    combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None)) and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = (list(rng.choice(combos)) + [None, None, None])[:3]
    name = getattr(args, "name", None) or rng.choice(["Boo", "Mina", "Pip", "Luna", "Nico"])
    return StoryParams(place=place, activity=activity, prize=prize, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), params.name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


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
        triples = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(StoryParams(*c, name="Boo")) for c in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
