#!/usr/bin/env python3
"""
storyworlds/worlds/cave_suspense_heartwarming.py
=================================================

A small, self-contained storyworld about a cave, a tense search, and a warm
happy ending.

The seed image is simple: someone goes into a cave, something goes missing, the
darkness feels scary, and a caring helper finds a gentle way through. The
simulation models that premise as state: darkness, cold, fear, wet stones,
courage, and comfort. The story is then narrated from those state changes, not
from a fixed paragraph template.

This world is intentionally narrow. The cave is the same kind of place every
time, but the exact child, helper, prize, and rescue tool can vary within
plausible bounds.
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
    carried_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
class Setting:
    place: str = "the cave"
    dark: bool = True
    echoey: bool = True
    wet: bool = True
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
    risk: str
    fear: str
    keyword: str
    zone: set[str]
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
    neediness: str = "careful"
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
    prep: str
    tail: str
    guards: set[str]
    covers: set[str]
    plural: bool = False
    protective: bool = True
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
        self.phase: str = "start"

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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        other = World(self.setting)
        other.entities = copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.fired = set(self.fired)
        other.phase = self.phase
        return other


def _r_wet_cold(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters["wet"] < THRESHOLD:
            continue
        sig = ("wet_cold", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["cold"] += 1
        out.append(f"The damp air made {actor.id} feel colder.")
    return out


def _r_fear(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes["fear"] < THRESHOLD:
            continue
        sig = ("fear_echo", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"The echo made the cave feel even bigger.")
    return out


CAUSAL_RULES = [
    _r_wet_cold,
    _r_fear,
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    actor.meters["wet"] += 1
    actor.memes["fear"] += 1
    actor.memes["courage"] += 1
    world.phase = "search"
    propagate(world, narrate=narrate)


def predict_risk(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {
        "fear": sim.get(actor.id).memes["fear"],
        "cold": sim.get(actor.id).meters["cold"],
        "damage": prize.meters["damage"],
    }


def setting_line(setting: Setting) -> str:
    if setting.dark and setting.echoey and setting.wet:
        return "The cave was dark, echoey, and cool, with little wet spots shining on the stone."
    if setting.dark:
        return "The cave was dark, and the stones held onto every sound."
    return "The cave was quiet in a careful, still way."


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who loved brave adventures.")
    world.say(f"{hero.pronoun().capitalize()} liked small surprises and safe places to come home to.")


def prize_intro(world: World, hero: Entity, prize: Entity) -> None:
    prize.carried_by = hero.id
    world.say(f"{hero.id} carried {hero.pronoun('possessive')} {prize.label} everywhere.")
    world.say(f"{hero.pronoun('possessive').capitalize()} {prize.label} was soft, special, and never left behind.")


def arrive(world: World, hero: Entity, helper: Entity, activity: Activity) -> None:
    world.say(f"One day, {hero.id} and {helper.id} went into {world.setting.place}.")
    world.say(setting_line(world.setting))


def start_search(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb}, but then {hero.pronoun('possessive')} "
        f"{prize.label} was no longer where it should be."
    )
    world.say(f"{hero.id} looked around and listened hard for a clue.")


def warn(world: World, helper: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_risk(world, hero, activity, prize.id)
    if pred["damage"] >= THRESHOLD:
        return False
    if pred["cold"] >= THRESHOLD:
        world.say(
            f'"The cave is chilly and the stones are slippery," {helper.id} said. '
            f'"Let\'s be careful before we go farther."'
        )
    else:
        world.say(f'"Stay close to me," {helper.id} said, keeping a warm hand near {hero.pronoun("object")}.')
    return True


def spook(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["fear"] += 1
    world.say(f"A long echo bounced through the tunnel, and {hero.id} felt a little scared.")
    world.say(f"{hero.pronoun().capitalize()} wanted to {activity.rush} and stop feeling lost.")


def comfort(world: World, helper: Entity, hero: Entity) -> None:
    hero.memes["comfort"] += 1
    hero.memes["hope"] += 1
    world.say(f"{helper.id} knelt beside {hero.id} and gave {hero.pronoun('object')} a steady smile.")
    world.say(f"\"We're together,\" {helper.id} said, and that made the cave feel less lonely.")


def choose_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.keyword in gear.guards and prize.region in gear.covers:
            return gear
    return None


def offer_gear(world: World, helper: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = choose_gear(activity, prize)
    if gear is None:
        return None
    world.say(
        f'{helper.id} found {gear.label} and said, "{gear.prep}."'
    )
    return gear


def accept(world: World, hero: Entity, helper: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["fear"] = 0.0
    hero.memes["hope"] += 1
    hero.memes["comfort"] += 1
    world.say(
        f"{hero.id} nodded and let {helper.id} help."
    )
    world.say(
        f'They {gear.tail}. Soon {hero.id} was {activity.gerund}, and {hero.pronoun("possessive")} {prize.label} was safe again.'
    )
    world.say(
        f"{helper.id} held the prize out with a smile, and {hero.id} hugged {helper.id} very tightly."
    )


def resolve_clue(world: World, hero: Entity, prize: Entity) -> None:
    prize.carried_by = hero.id
    prize.meters["damage"] = 0
    world.phase = "found"
    world.say(f"At last, {hero.id} spotted {hero.pronoun('possessive')} {prize.label} tucked beside a flat stone.")
    world.say(f"{hero.id} picked {prize.it()} up carefully, as gently as if it were a sleeping kitten.")


def finish(world: World, hero: Entity, helper: Entity, prize: Entity) -> None:
    world.phase = "home"
    world.say(
        f"When they left the cave, the cave behind them was still dark, but {hero.id}'s heart was bright."
    )
    world.say(
        f"{hero.id} carried {hero.pronoun('possessive')} {prize.label} home, and {helper.id} walked close enough to make the way feel warm."
    )
    world.say(
        f"That night, {hero.id} smiled at the safe little {prize.label} and knew brave things could end in hugs."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=helper.id,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    prize_intro(world, hero, prize)
    world.para()
    arrive(world, hero, helper, activity)
    start_search(world, hero, activity, prize)
    warn(world, helper, hero, activity, prize)
    spook(world, hero, activity)
    comfort(world, helper, hero)
    gear = offer_gear(world, helper, hero, activity, prize)
    if gear is not None:
        accept(world, hero, helper, activity, prize, gear)
    world.para()
    resolve_clue(world, hero, prize)
    finish(world, hero, helper, prize)

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        prize_cfg=prize_cfg,
        activity=activity,
        setting=setting,
        gear=gear,
        found=True,
    )
    return world


SETTINGS = {
    "cave": Setting(place="the cave", dark=True, echoey=True, wet=True, affords={"search", "follow", "listen"}),
}

ACTIVITIES = {
    "search": Activity(
        id="search",
        verb="search for the missing prize",
        gerund="searching carefully",
        rush="run deeper into the tunnel",
        risk="darkness and wet stones",
        fear="the cave felt too big",
        keyword="search",
        zone={"hands", "feet"},
        tags={"cave", "dark", "wet", "search"},
    ),
    "follow": Activity(
        id="follow",
        verb="follow the echo",
        gerund="following the echo",
        rush="dash after the sound",
        risk="the echo could lead them farther in",
        fear="the tunnel was hard to read",
        keyword="echo",
        zone={"feet"},
        tags={"cave", "echo", "dark"},
    ),
    "listen": Activity(
        id="listen",
        verb="listen for the tiny clue",
        gerund="listening very hard",
        rush="hurry toward the drip",
        risk="the drip could hide the right path",
        fear="every sound blended together",
        keyword="drip",
        zone={"ears"},
        tags={"cave", "echo", "dark", "listen"},
    ),
}

PRIZES = {
    "bunny": Prize(label="bunny", phrase="a soft stuffed bunny", type="toy", region="hands", plural=False, neediness="gentle"),
    "blanket": Prize(label="blanket", phrase="a small blue blanket", type="blanket", region="hands", plural=False, neediness="gentle"),
    "drum": Prize(label="drum", phrase="a little hand drum", type="toy", region="hands", plural=False, neediness="careful"),
}

GEAR = [
    Gear(id="lantern", label="a lantern", prep="Let's take this lantern so the dark won't feel so big", tail="followed the lantern light back along the path", guards={"search", "follow", "listen"}, covers={"hands", "feet"}),
    Gear(id="rope", label="a soft rope", prep="Let's use a soft rope so we can stay close together", tail="stayed tied together and walked slowly toward the tunnel mouth", guards={"search", "follow"}, covers={"hands", "feet"}),
    Gear(id="cloak", label="a warm cloak", prep="Let's put on a warm cloak so the cave air won't feel so cold", tail="wrapped the cloak around the child and walked home gently", guards={"search", "follow", "listen"}, covers={"hands", "feet", "body"}),
]

GIRL_NAMES = ["Mia", "Luna", "Nora", "Eli", "Ruby", "Hazel"]
BOY_NAMES = ["Finn", "Theo", "Leo", "Max", "Noah", "Owen"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    helper: str
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
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if choose_gear(act, prize) is not None:
                    combos.append((place, act_id, prize_id))
    return combos


KNOWLEDGE = {
    "cave": [("What is a cave?", "A cave is a hollow space in rock, often dark and cool, where people can go exploring.")],
    "echo": [("What is an echo?", "An echo is a sound that bounces off walls and comes back to your ears.")],
    "lantern": [("What does a lantern do?", "A lantern gives light so people can see in dark places.")],
    "rope": [("What is a rope for?", "A rope can help people hold on, pull things, or stay safely together.")],
    "warm": [("Why do warm clothes help?", "Warm clothes help keep your body from feeling chilly when the air is cold.")],
    "search": [("What do you do when you search for something?", "When you search, you look carefully in more than one place until you find what is missing.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, act, prize = f["hero"], f["helper"], f["activity"], f["prize_cfg"]
    return [
        f'Write a gentle suspense story for a young child about a cave, a missing {prize.label}, and a kind helper.',
        f"Tell a heartwarming story where {hero.id} goes into {world.setting.place} and needs help finding {hero.pronoun('possessive')} {prize.label}.",
        f'Write a short story that includes the word "{act.keyword}" and ends with a safe, warm feeling after the dark cave search.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, act = f["hero"], f["helper"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who went into {world.setting.place} to look for the missing {prize.label}?",
            answer=f"{hero.id} went into {world.setting.place} with {helper.id} to look for the missing {prize.label}.",
        ),
        QAItem(
            question=f"Why did the cave search feel scary at first?",
            answer=f"It felt scary because the cave was dark, echoey, and wet, so every step and sound felt bigger than usual.",
        ),
        QAItem(
            question=f"What helped {hero.id} keep going instead of giving up?",
            answer=f"{helper.id} stayed close, spoke softly, and brought a helpful tool so {hero.id} could keep searching safely.",
        ),
        QAItem(
            question=f"What was special about the {prize.label} at the end?",
            answer=f"The {prize.label} was found safe again, and {hero.id} could carry {hero.pronoun('possessive')} special prize home.",
        ),
    ]
    if f.get("gear") is not None:
        gear = _safe_fact(world, f, "gear")
        qa.append(
            QAItem(
                question=f"How did {gear.label} help in the cave?",
                answer=f"{gear.label.capitalize()} helped because it gave the child a safer, easier way to keep going in the dark cave.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    out: list[QAItem] = []
    for tag in ["cave", "echo", "lantern", "rope", "warm", "search"]:
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="cave", activity="search", prize="bunny", name="Mia", gender="girl", helper="mother"),
    StoryParams(place="cave", activity="follow", prize="blanket", name="Finn", gender="boy", helper="father"),
    StoryParams(place="cave", activity="listen", prize="drum", name="Luna", gender="girl", helper="aunt"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: the cave search does not have a sensible tool for a {prize.label} in this setup.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(_safe_lookup(PRIZES, prize_id).genders))
    return f"(No story: a {_safe_lookup(PRIZES, prize_id).label} isn't a typical {gender}'s item here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(A, P) :- activity(A), prize(P), affords(cave, A), worn_on(P, hands).
fixes(G, A, P) :- gear(G), prize_at_risk(A, P), guards(G, A), covers(G, hands).
valid(cave, A, P) :- prize_at_risk(A, P), fixes(_, A, P).
valid_story(cave, A, P, G) :- valid(cave, A, P), wears(G, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for a in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, a))
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
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: cave suspense with a heartwarming ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "aunt", "uncle"])
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
    if getattr(args, "activity", None) and getattr(args, "prize", None):
        act, pr = _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if choose_gear(act, pr) is None:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "prize", None) and getattr(args, "gender", None) not in _safe_lookup(PRIZES, getattr(args, "prize", None)).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
              and (getattr(args, "gender", None) is None or getattr(args, "gender", None) in PRIZES[c[2]].genders)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, activity, prize_id = rng.choice(list(combos))
    prize = _safe_lookup(PRIZES, prize_id)
    gender = getattr(args, "gender", None) or rng.choice(sorted(prize.genders))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["mother", "father", "aunt", "uncle"])
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.helper)
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
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:9} {act:8} {prize:8}  [{', '.join(genders)}]")
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
