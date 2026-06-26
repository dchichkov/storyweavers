#!/usr/bin/env python3
"""
storyworlds/worlds/mistralai_mistral-small-2603_service_20260625T020146Z_seed424242_n50/nozzle_bad_ending_curiosity_tall_tale.py
================================================================================

A standalone *tall tale* story world centered around a magical nozzle whose
excessive curiosity leads to a bad ending. Features a three-act narrative arc:
wonder, overuse, and ruin. Physical meters ("strange") and emotional memes
("curiosity", "pride") drive the prose via forward-chained causal rules.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

# MAGIC threshold where consequences become narrated
THRESHOLD = 2.0

# Regions and mess kinds for nozzle physics
REGIONS = {"hands", "face", "clothes"}
MESS_KINDS = {"strange", "shimmer", "bubbly", "sparkly"}

# Exponentially rising danger curve for the "Bad Ending" arc
DANGER_CURVE = {1: 1.0, 2: 2.0, 3: 5.0, 4: 9.0, 5: 16.0}


# ---------------------------------------------------------------------------
# Entities: the magical nozzle and the curious explorer
# ---------------------------------------------------------------------------

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
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held: bool = False
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    actuator: object | None = None
    hero: object | None = None
    nozzle: object | None = None
    prize_real: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "witch", "aunt"}
        male = {"boy", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"witch": "granny", "uncle": "uncle"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# World setting and parameters
# ---------------------------------------------------------------------------
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
    place: str = "the backyard"
    indoor: bool = False
    magical: bool = False
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
    zone: set[str]
    keyword: str = ""
    tags: set[str] = field(default_factory=set)

    def warn(self) -> str:
        return {
            "squirt": '"Let me show you how it works first,"',
            "blast": '"This is powerful magic—follow my lead!"',
            "drip": '"No empty promises about this pipe!"',
        }.get(self.id, '"Careful now!')
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
    region: str = "clothes"
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


# ---------------------------------------------------------------------------
# World: entity store + narration history
# ---------------------------------------------------------------------------
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.magical_aura: float = 0.0

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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.magical_aura = self.magical_aura
        return clone


# ---------------------------------------------------------------------------
# Causal rules: forward-chained chaotic magic
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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


def _r_too_curios(world: World) -> list[str]:
    """Curiosity beyond threshold → pride spike → reckless squirt attempts."""
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["curiosity"] < THRESHOLD:
            continue
        if actor.memes["pride"] < THRESHOLD:
            continue
        if ("chaos", actor.id) in world.fired:
            continue
        world.fired.add(("chaos", actor.id))
        actor.memes["chaos"] += 1
        out.append(
            f"{actor.pronoun().capitalize()} stared at the nozzle with wide eyes, "
            "pulsing with curiosity so fierce it threatened to burst forth!"
        )
    return out


def _r_squirt_mess(world: World) -> list[str]:
    """Pointing nozzle at surfaces creates exponentially messy outcomes."""
    out: list[str] = []
    nozzle = None
    for e in list(world.entities.values()):
        if e.id == "nozzle" and e.held:
            nozzle = e
            break
    if not nozzle:
        return out

    actuators = world.get("actuator") if "actuator" in world.entities else None
    if actuators:
        danger = actuators.meters["strange"]
    else:
        danger = nozzle.meters["strange"]

    for actor in world.characters():
        if danger < THRESHOLD:
            continue
        for region in REGIONS:
            if actor.memes.get("resolve", 0.0) >= danger * 0.5:
                continue
            sig = ("splash", actor.id, region)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.meters["strange"] += DANGER_CURVE[min(5, int(danger))]
            out.append(
                f"Suddenly {actor.pronoun('subject')} was drenched in "
                f"{nozzle.memes.get('outcome','messy')}, "
                f"making {actor.pronoun('possessive')} {region} glimmer "
                f"with every step!"
            )
    return out


def _r_bad_ending(world: World) -> list[str]:
    """Irreversible climax when magical aura exceeds 20."""
    if world.magical_aura < 20:
        return []
    nozzle = world.entities.get("nozzle")
    if not nozzle or nozzle.meters.get("strange", 0) < 30:
        return []
    if ("end",) in world.fired:
        return []
    world.fired.add(("end",))
    return [
        "__ENDING__",
        "The backyard shimmered, the nozzle roared, and everything became "
        "a tangled, sparkling nightmare! The once-simple errand turned into "
        "a lesson carved in brilliance and chaos."
    ]


CAUSAL_RULES: list[Rule] = [
    Rule(name="curiosity", tag="emotional", apply=_r_too_curios),
    Rule(name="squirt", tag="physical", apply=_r_squirt_mess),
    Rule(name="bad_end", tag="climax", apply=_r_bad_ending),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                if sents[0] == "__ENDING__":
                    world.paragraphs[-1].append(sents[1])
                    world.paragraphs[-1].append(sents[2])
                    world.paragraphs.append([])
                    changed = False
                    break
                changed = True
                produced.extend(s for s in sents if s != "__ENDING__")
    if narrate and not any("__ENDING__" in s for s in produced):
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def too_dangerous(activity: Activity) -> bool:
    """Nozzle activities never safe beyond first attempt."""
    return True

def predict_danger(world: World, actor: Entity, activity: Activity) -> float:
    sim = world.copy()
    _do_activity(sim, actor, activity, narrate=False)
    return sim.magical_aura

# ---------------------------------------------------------------------------
# Screenplay verbs (tall tale exaggerations)
# ---------------------------------------------------------------------------
def magical_detail(activity: Activity) -> str:
    return {
        "squirt": "a gushing arc of pure magic liquid",
        "blast": "a thunderous fizz of golden sparks",
        "drip": "perfectly timed droplets that hummed like tiny chimes",
    }.get(activity.id, "sparkling surprises")

def setting_twist(setting: Setting, activity: Activity) -> str:
    if setting.magical:
        return ("Beneath the saucer moon of a mushroom night, "
                "the backyard hummed with latent sorcery.")
    return "Beneath the bright summer sun, ordinary things felt quietly magical."

def prize_was_tarnished(hero: Entity, prize: Entity) -> str:
    return (f"{hero.pronoun('possessive').capitalize()} {prize.label} "
            "glimmered no more, now forever threaded with rogue enchantment.")

def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    nozzle = world.entities["nozzle"]
    nozzle.held = True
    actor.memes["curiosity"] += 1.5
    actor.memes["pride"] += 0.5
    world.magical_aura += 1.0
    nozzle.meters["strange"] += 1.0
    if actor.memes["curiosity"] > THRESHOLD:
        nozzle.memes["outcome"] = "uncontrollable"
    propagate(world, narrate=narrate)

def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"In a cozy corner of {world.setting.place}, "
        f"a {hero.type} named {hero.id} spotted something glinting."
    )
    world.say(
        f"It was {hero.pronoun('possessive')} lucky day: "
        "a nozzle that whispered promises of wondrous squirts!"
    )

def marvel_nozzle(world: World, hero: Entity) -> None:
    hero.memes["curiosity"] += 2.0
    world.say(
        f"Gasping, {hero.id} picked up the nozzle. "
        "The metal shimmered with letters no one could quite read."
    )

def ponder_risk(world: World, hero: Entity, prize: Entity) -> bool:
    pred = predict_danger(world, hero, ACTIVITIES["squirt"])
    if pred < 10:
        return False
    world.facts["predicted_danger"] = pred
    world.say(
        f'"This nozzle is more than it seems," {hero.id} murmured, '
        f'gazing at {hero.pronoun("possessive")} {prize.phrase}. '
        '"Should I even touch it?"'
    )
    return True

def ignore_warning(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1.5
    world.say(
        f"Still, curiosity flared like a newly lit bulb. "
        f"{hero.pronoun().capitalize()} decided to try anyway!"
    )
    _do_activity(world, hero, activity)

def disaster(world: World, hero: Entity) -> None:
    hero.memes["regret"] = 1.0
    world.say(
        f"The nozzle let loose a jet of rogue magic! "
        f"{hero.pronoun().capitalize()} tried to shut it off, but the magic "
        "had learned to giggle—and would not be silenced."
    )
    propagate(world, narrate=True)

def reflect(world: World, hero: Entity) -> None:
    hero.memes["resolve"] += 3.0
    world.para()
    world.say(
        f"Later, with {hero.pronoun('possessive')} "
        f"{hero.it()} still shimmering slightly, {hero.id} vowed "
        "never again to follow raw wonder without a drop of caution."
    )

def tell(setting: Setting, hero_name: str = "Mira", hero_type: str = "girl",
         trait: str = "curious", prize: Prize | None = None) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["small", trait],
        label=hero_name,
    ))
    prize_real = world.add(Entity(
        id="prize", type=prize.type if prize else "shirt",
        label=prize.label if prize else "play shirt",
        phrase=prize.phrase if prize else "favorite sunny-day shirt",
        owner=hero.id, region=prize.region if prize else "clothes",
        plural=prize.plural if prize else False,
    ))
    nozzle = world.add(Entity(
        id="nozzle", kind="thing", type="nozzle",
        label="mystic nozzle", phrase="an ancient brass nozzle",
        held=False, region="hands",
    ))
    actuator = world.add(Entity(
        id="actuator", kind="thing", type="actuator", label="operating lever",
        held=True,
    ))

    # Act 1 – Wonder: discovery of the nozzle
    introduce(world, hero)
    world.para()
    marvel_nozzle(world, hero)

    # Act 2 – Conflict: risk vs. curiosity
    world.para()
    ponder_risk(world, hero, prize_real) or ignore_warning(world, hero, ACTIVITIES["squirt"])

    # Act 3 – Climax & Resolution: disastrous squirt → hard lesson
    world.para()
    disaster(world, hero)
    reflect(world, hero)

    # Facts for Q&A
    world.facts.update(
        hero=hero, prize=prize_real, nozzle=nozzle, actuator=actuator,
        curiosity=hero.memes["curiosity"] >= THRESHOLD,
        regret=hero.memes.get("regret", 0) > 0,
        dangerous=nozzle.meters["strange"] >= 15,
        resolved=hero.memes.get("resolve", 0) >= 3
    )
    return world

# ---------------------------------------------------------------------------
# Registries and valid combinations
# ---------------------------------------------------------------------------
SETTINGS = {
    "backyard": Setting(place="the backyard", indoor=False, magical=True),
    "garage": Setting(place="the garage", indoor=True, magical=False),
    "workshop": Setting(place="the workshop", indoor=True, magical=True),
}

ACTIVITIES = {
    "squirt": Activity(
        id="squirt",
        verb="squirt from the nozzle",
        gerund="squirting wonder",
        rush="aim the nozzle straight up",
        mess="strange",
        zone={"hands", "face", "clothes"},
        keyword="nozzle",
        tags={"magic", "water", "curiosity"},
    ),
    "blast": Activity(
        id="blast",
        verb="shoot a blast of magic",
        gerund="blasting golden arcs",
        rush="pull the lever fast",
        mess="shimmer",
        zone={"hands", "face"},
        keyword="levers",
        tags={"sparkle", "noise"},
    ),
    "drip": Activity(
        id="drip",
        verb="let perfect drops fall",
        gerund="dripping enchanted pearls",
        rush="wait patiently",
        mess="sparkly",
        zone={"clothes"},
        keyword="drops",
        tags={"gentle", "shiny"},
    ),
}

PRIZES = {
    "shirt": Prize(
        label="shirt",
        phrase="sunshine-yellow shirt",
        region="clothes",
    ),
    "hat": Prize(
        label="hat",
        phrase="new straw hat",
        region="face",
    ),
    "apron": Prize(
        label="apron",
        phrase="old flowered apron",
        region="clothes",
        plural=False,
    ),
}

GIRL_NAMES = ["Mira", "Lumi", "Zara", "Nova"]
BOY_NAMES = ["Finn", "Remy", "Juno", "Echo"]

TRAITS = ["curious", "bold", "daring", "inquisitive"]

def valid_combos() -> list[tuple[str, str]]:
    return [("backyard", "squirt"), ("workshop", "blast"), ("backyard", "drip")]

# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    activity: str
    prize: str
    name: str
    gender: str
    trait: str
    seed: int | None = None

# ---------------------------------------------------------------------------
# Q&A generation – tall-tale style explanations
# ---------------------------------------------------------------------------
    params: object | None = None
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
    "magic_nozzle": [
        ("What is a magnetic nozzle?",
         "A nozzle is a spout shaped like a horn that shoots liquid; "
         "a magnetic version sucks up water then sprays it as sparkling pictures."),
        ("Can a nozzle be alive?",
         "When bathed in moonlight and used with wonder, certain old nozzles "
         "begin to giggle and choose their favorite curators."),
        ("Why do some nozzles make clothes shimmer?",
         "Their liquid carries tiny mirrors aligning with starlight—so when "
         "you move, they flash like fireflies across fabric."),
    ],
    "curiosity": [
        ("Why do we feel curious?",
         "Curiosity is your mind’s sparkle, urging you to poke around dark corners "
         "until every secret feels safe to hold."),
        ("Can curiosity be too much?",
         "Yes—when curiosity outweighs caution, it’s like holding a live wire: "
         "you learn, but the lesson will glow forever."),
    ],
    "tall_tale": [
        ("What is a tall tale?",
         "A tall tale is a fib blown up until every thread feels magical and "
         "every shadow laughs back at you."),
        ("Can a story really tarnish your shirt?",
         "Only if the shirt believes in enchanted water—once it does, "
         "it glows and never fades, just like your memory of the afternoon."),
    ],
}

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    prize = _safe_fact(world, f, "prize")
    act = world.facts.get("activity")
    tag = act.keyword if act else "nozzle"
    return [
        f'Compose a tall children’s tale (ages 5-8) around the discovery of a '
        f'“living” nozzle that thrills but ultimately teaches costly curiosity.',
        f"Write a {{age}}-year-old’s bedtime fable starring {hero.id}, "
        f"who finds {hero.pronoun('possessive')} curiosity too great to resist "
        f"when faced with the ancient nozzle at the edge of the yard.",
        f'Include the phrase "shimmered with restless courage" and treat '
        f'the nozzle as a character with at least one mischievous giggle.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    prize = _safe_fact(world, f, "prize")
    sub = hero.pronoun("subject")
    pos = hero.pronoun("possessive")
    obj = hero.pronoun("object")
    qa: list[QAItem] = [
        QAItem(
            question="Who is the story really about?",
            answer=(
                f"It is about {pos} small {hero.type} named {hero.id}. "
                "One ordinary afternoon {sub} discovered a mysterious nozzle "
                "that hummed when held."
            ),
        ),
        QAItem(
            question="What did the nozzle do that felt magical?",
            answer=(
                f"The nozzle spouted liquid that made everything it touched "
                f"twinkle like stardust. {sub} could not look away!"
            ),
        ),
    ]
    if f.get("curiosity"):
        qa.append(QAItem(
            question="Why did the main character use the nozzle anyway?",
            answer=(
                f"{sub.capitalize()} wanted to feel the shimmer for {pos}self, "
                "even though {obj} remembered warnings. The curiosity "
                "grew too heavy to ignore."
            ),
        ))
    if f.get("dangerous"):
        qa.append(QAItem(
            question="What was the final lesson of this adventure?",
            answer=(
                f"{hero.id} learned that some wonders aren't gifts unless "
                f"handled with care. The glimmering clothes and wide eyes "
                f"reminded {obj} every day."
            ),
        ))
    if f.get("resolved"):
        qa.append(QAItem(
            question="How did the story end?",
            answer=(
                f"{hero.id} stored the nozzle far away and "
                "swore to ask questions first next time. "
                f"Only then did {hero.pronoun('subject')} sleep quietly again."
            ),
        ))
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"magic_nozzle", "curiosity"}
    out: list[QAItem] = []
    for tag in ["magic_nozzle", "curiosity", "tall_tale"]:
        for q, a in KNOWLEDGE.get(tag, []):
            out.append(QAItem(question=q, answer=a))
    return out

def format_qa(sample: StorySample) -> str:
    lines = ["== Tall Tale Q&A ==\n"]
    lines.append("Prompts that could have sparked this story:")
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\nQuestions you can answer just from this story:")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\nQuestions any child can answer about elements in this world:")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# CLI, validation, and ASP twin
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- magical ledger ---"]
    for e in list(world.entities.values()):
        ms = {k: f"{v:.1f}" for k, v in e.meters.items() if v > 0}
        mems = {k: f"{v:.1f}" for k, v in e.memes.items() if v > 0}
        bits = []
        if ms:
            bits.append(f"meters={ms}")
        if mems:
            bits.append(f"memes={mems}")
        if e.held:
            bits.append("held")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} {bits or '(idle)'}")
    lines.append(f"  magical_aura={world.magical_aura:.1f}")
    lines.append(f"  fired: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)

ASP_RULES = r"""
% A nozzle story is valid when the hero discovers the nozzle,
% feels curiosity strong enough to act, and the climax sparks illumination.
%
% Facts are emitted by asp_facts() from the registries above.
% Clauses below mirror the Python check "valid_combos".

curious_enough(H) :- meme(H,curiosity,C), C >= 2.
aware_of_risk(P) :- prize(P), actor(H), warned(H,P).
will_act(H,P) :- curious_enough(H), not avoid_risk(H).
bad_ending :- outcome(nozzle, chaos), magical_aura >= 20.

valid_story(Setting, Activity) :-
    setting(Setting), activity(Activity),
    curious_enough(hero), will_act(hero, prize), bad_ending.

#show valid_story/2.
"""

def asp_facts() -> str:
    import asp  # lazy import
    lines: list[str] = []
    lines.append(asp.fact("setting", "backyard"))
    lines.append(asp.fact("setting", "garage"))
    lines.append(asp.fact("setting", "workshop"))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("wears", "girl" if pid != "hat" else "boy", pid))
    for name in GIRL_NAMES + BOY_NAMES:
        lines.append(asp.fact("hero_name", name))
    for t in TRAITS:
        lines.append(asp.fact("trait", t))
    return "\n".join(lines)

def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    py_valid = set(valid_combos())
    asp_valid = set(asp.atoms(asp.one_model(asp_program("#show valid_story/2.")), "valid_story"))
    if py_valid == asp_valid:
        print(f"✓ Tall-tale logic verified ({len(py_valid)} valid combinations).")
        return 0
    print("⚠️  Tall-tale gates drift between Python and ASP!")
    return 1

# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nozzle Tall Tale: a curious child, a whispering nozzle, "
                    "a sparkly bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "activity", None) and too_dangerous(_safe_lookup(ACTIVITIES, getattr(args, "activity", None))):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "prize", None) and getattr(args, "gender", None) not in {"girl", "boy"}:
        raise ValueError("Gender must be 'girl' or 'boy' in this domain.")

    candidates = [(s, a) for s in SETTINGS for a in ACTIVITIES]
    if getattr(args, "place", None):
        candidates = [(p, a) for p, a in candidates if p == getattr(args, "place", None)]
    if getattr(args, "activity", None):
        candidates = [(p, a) for p, a in candidates if a == getattr(args, "activity", None)]

    place, activity = rng.choice(candidates)
    prize = rng.choice(list(PRIZES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        setting=place,
        activity=activity,
        prize=prize,
        name=name,
        gender=gender,
        trait=trait,
    )

def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        params.name, "girl" if params.gender == "girl" else "boy",
        params.trait,
        _safe_lookup(PRIZES, params.prize) if params.prize else None,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print(format_qa(sample))

def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program(""))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        models = asp.atoms(asp.one_model(asp_program("#show valid_story/2.")), "valid_story")
        print(f"Magically compatible stories: {len(models)}\n")
        for place, act in models:
            print(f"  • a {act} tale set in {place}")
        return

    base_seed = getattr(args, "seed", None) or random.randrange(2 ** 31)
    rng = random.Random(base_seed)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for i, (pl, act) in enumerate(valid_combos()):
            params = StoryParams(
                setting=pl, activity=act, prize="shirt",
                name="Mira", gender="girl", trait="curious", seed=i,
            )
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            i += 1
            try:
                params = resolve_params(args, rng)
            except Exception as err:
                print(err)
                return
            params.seed = base_seed + i
            sample = generate(params)
            key = (sample.story, params.prize)
            if key in seen:
                continue
            seen.add(key)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}’s {p.activity} tragedy in {p.setting}\n"
        elif len(samples) > 1:
            header = f"### variant {i + 1}\n"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
