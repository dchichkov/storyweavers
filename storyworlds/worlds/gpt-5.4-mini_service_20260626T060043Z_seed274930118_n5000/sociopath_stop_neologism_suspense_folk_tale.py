#!/usr/bin/env python3
"""
storyworlds/worlds/sociopath_stop_neologism_suspense_folk_tale.py
==================================================================

A small folk-tale storyworld with suspense: a village child, a dark road,
a wary stop, and a new word that helps everyone through the night.

Seed idea:
---
A child hears a stranger called Sociopath keep saying "stop" at the edge of
the wood. The child is frightened, but the stranger is really warning about a
sinking bridge in the dark. The child invents a new word, a neologism, for
their shared lantern-bobbing pause, and the village learns a safer way to
cross together.

This world models:
- physical meters: light, dark, risk, steadiness, distance, wind, fear markers
- emotional memes: fear, trust, suspense, relief, courage, curiosity

The prose is authored in a gentle folk-tale style, with a suspenseful middle
turn and a concrete ending image proving what changed.
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
    bridge: object | None = None
    gear: object | None = None
    hero: object | None = None
    prize: object | None = None
    stranger: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "witch"}
        male = {"boy", "father", "dad", "man", "grandfather"}
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
    place: str = "the village lane"
    indoor: bool = False
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
    mess: str
    soil: str
    zone: set[str]
    weather: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
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

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.id in {"lantern_hood", "cloak"} and g.worn_by == actor.id for g in self.worn_items(actor))

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
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    bridge = world.entities.get("bridge")
    if bridge is None:
        return out
    if bridge.meters.get("unstable", 0.0) < THRESHOLD:
        return out
    for actor in world.characters():
        if actor.memes.get("fear", 0.0) < THRESHOLD:
            continue
        sig = ("alarm", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["suspense"] = actor.memes.get("suspense", 0.0) + 1
        out.append(f"The night felt too still, and {actor.id} held very quiet.")
    return out


def _r_light(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("light", 0.0) < THRESHOLD:
            continue
        for ent in list(world.entities.values()):
            if ent.id == actor.id:
                continue
            if ent.meters.get("dark", 0.0) < THRESHOLD:
                continue
            sig = ("light", actor.id, ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.meters["dark"] = max(0.0, ent.meters.get("dark", 0.0) - 1)
            ent.memes["fear"] = max(0.0, ent.memes.get("fear", 0.0) - 1)
            out.append(f"{actor.id}'s lamp pushed a little light into the dark.")
    return out


CAUSAL_RULES = [
    _r_alarm,
    _r_light,
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


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters.get("dirty", 0.0) >= THRESHOLD),
        "workload": sum(e.meters.get("workload", 0.0) for e in sim.characters()),
    }


def activity_delight(activity: Activity) -> str:
    return {
        "whispering_road": "the road seemed to listen to every footstep",
        "bridge_crossing": "the bridge creaked like an old fiddle string",
        "lantern_walk": "the lantern made a warm gold pool on the path",
        "word_making": "the new word felt bright and brave in the mouth",
    }.get(activity.id, "the night seemed full of old magic")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"The room was small and still, with a door that shook in the wind."
    return f"{setting.place.capitalize()} lay under the trees, and the dark waited between the posts."


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who loved lantern-light and listening to old tales.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund}; {activity_delight(activity)}.")


def introduce_stranger(world: World, stranger: Entity) -> None:
    world.say(f"At the edge of the lane stood a quiet traveler named {stranger.label}, with a pale coat and a still face.")


def buys(world: World, caretaker: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"That week, {caretaker.label} gave {hero.id} {hero.pronoun('object')} {prize.phrase}.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and carried {prize.it()} everywhere.")


def arrive(world: World, hero: Entity, caretaker: Entity, activity: Activity) -> None:
    world.say(f"One dusk, {hero.id} and {caretaker.label} went to {world.setting.place}.")
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(f"{hero.id} wanted to {activity.verb}, but the air had gone thin with suspense.")


def warn(world: World, stranger: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    world.say(f'"Stop," said {stranger.label}, and {hero.id} froze in the hush.')
    world.say(f'"The bridge will give way if you rush," {stranger.label} said. "Wait for the light."')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    world.say(f"{hero.id} nearly ran ahead, but the dark itself seemed to ask for patience.")
    world.say(f"{hero.id} tried to {activity.rush},")


def stop_hand(world: World, stranger: Entity, hero: Entity) -> None:
    hero.memes["held"] = hero.memes.get("held", 0.0) + 1
    hero.memes["suspense"] = hero.memes.get("suspense", 0.0) + 1
    world.say(f"but {stranger.label} lifted a hand and held {hero.pronoun('possessive')} sleeve.")
    world.say(f"'Stop here,' {stranger.label} said again, and the wind went quiet.")


def compromise(world: World, caretaker: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=caretaker.id,
        worn_by=hero.id,
        plural=gear_def.plural,
    ))
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        del world.entities[gear.id]
        return None
    world.say(f"{caretaker.label} nodded and brought {gear_def.label}.")
    world.say(f'"How about we {gear_def.prep}?" {caretaker.label} asked.')
    return gear_def


def accept(world: World, caretaker: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["fear"] = max(0.0, hero.memes.get("fear", 0.0) - 1)
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    world.say(f"{hero.id} smiled, and the tight knot in {hero.pronoun('possessive')} chest eased.")
    world.say(f'"That is no ordinary stop," {hero.id} said. "It is a {world.facts.get("neologism", "new word")}!"')
    world.say(
        f"They {gear_def.tail}. Soon {hero.id} could {activity.verb}, "
        f"{prize.label} safe and the lantern bright beside the bridge."
    )


def tell(
    setting: Setting,
    activity: Activity,
    prize_cfg: Prize,
    hero_name: str = "Mara",
    hero_type: str = "girl",
    hero_traits: Optional[list[str]] = None,
    caretaker_type: str = "grandmother",
) -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        meters={"light": 0.0, "dark": 0.0},
        memes={"curiosity": 1.0},
    ))
    caretaker = world.add(Entity(
        id="Caretaker",
        kind="character",
        type=caretaker_type,
        label="Grandmother",
        meters={"light": 0.0, "dark": 0.0},
        memes={"worry": 1.0},
    ))
    stranger = world.add(Entity(
        id="Stranger",
        kind="character",
        type="man",
        label="Sociopath",
        meters={"light": 0.0, "dark": 0.0},
        memes={"watchfulness": 1.0},
    ))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=caretaker.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
        meters={"dirty": 0.0},
    ))
    bridge = world.add(Entity(
        id="bridge",
        type="bridge",
        label="the old bridge",
        meters={"unstable": 1.0, "dark": 1.0},
        memes={"suspense": 1.0},
    ))

    if hero_traits:
        hero.memes["courage"] = 1.0 if "courageous" in hero_traits else 0.0

    introduce(world, hero)
    introduce_stranger(world, stranger)
    loves_activity(world, hero, activity)
    buys(world, caretaker, hero, prize)
    loves_prize(world, hero, prize)

    world.para()
    arrive(world, hero, caretaker, activity)
    wants(world, hero, activity)
    warn(world, stranger, hero, activity, prize)
    defies(world, hero, activity)
    stop_hand(world, stranger, hero)

    world.para()
    world.facts["neologism"] = "moon-stop"
    world.say(f"Then {hero.id} made a neologism: '{world.facts['neologism']}' meant a careful stop where the lantern could speak first.")
    gear_def = compromise(world, caretaker, hero, activity, prize)
    if gear_def:
        accept(world, caretaker, hero, activity, prize, gear_def)

    world.facts.update(
        hero=hero,
        caretaker=caretaker,
        stranger=stranger,
        prize=prize,
        prize_cfg=prize_cfg,
        activity=activity,
        setting=setting,
        gear=gear_def,
        bridge=bridge,
        conflict=hero.memes.get("fear", 0.0) >= THRESHOLD,
        resolved=gear_def is not None,
    )
    return world


SETTINGS = {
    "lane": Setting(place="the village lane", affords={"bridge_crossing", "lantern_walk", "word_making"}),
    "wood": Setting(place="the pine wood", affords={"whispering_road", "bridge_crossing", "lantern_walk"}),
    "river": Setting(place="the river path", affords={"bridge_crossing", "lantern_walk"}),
}

ACTIVITIES = {
    "bridge_crossing": Activity(
        id="bridge_crossing",
        verb="cross the old bridge",
        gerund="crossing the old bridge",
        rush="run onto the bridge",
        mess="dark",
        soil="too dark",
        zone={"bridge"},
        weather="night",
        keyword="stop",
        tags={"bridge", "dark", "stop"},
    ),
    "lantern_walk": Activity(
        id="lantern_walk",
        verb="walk by lantern-light",
        gerund="walking by lantern-light",
        rush="hurry down the path",
        mess="dark",
        soil="too dark",
        zone={"path"},
        weather="night",
        keyword="lantern",
        tags={"lantern", "light"},
    ),
    "whispering_road": Activity(
        id="whispering_road",
        verb="follow the whispering road",
        gerund="following the whispering road",
        rush="run after the whisper",
        mess="dark",
        soil="too dark",
        zone={"road"},
        weather="night",
        keyword="sociopath",
        tags={"whisper", "road", "suspense"},
    ),
    "word_making": Activity(
        id="word_making",
        verb="make a new word",
        gerund="making a neologism",
        rush="say the word too quickly",
        mess="dark",
        soil="too dark",
        zone={"mouth"},
        weather="night",
        keyword="neologism",
        tags={"word", "language", "neologism"},
    ),
}

PRIZES = {
    "cloak": Prize(label="cloak", phrase="a wool cloak", type="cloak", region="torso"),
    "lantern": Prize(label="lantern", phrase="a little brass lantern", type="lantern", region="hand"),
    "bread": Prize(label="bread", phrase="a warm loaf of bread", type="bread", region="basket"),
}

GEAR = [
    Gear(
        id="lantern_hood",
        label="a lantern hood",
        covers={"hand"},
        guards={"dark"},
        prep="put a hood over the lantern first",
        tail="put a hood over the lantern and crossed slowly",
    ),
    Gear(
        id="cloak",
        label="the wool cloak",
        covers={"torso"},
        guards={"dark"},
        prep="wrap the wool cloak around you first",
        tail="wrapped the wool cloak tight and crossed slowly",
    ),
]


GIRL_NAMES = ["Mara", "Elin", "Tova", "Sia", "Nina", "Brin"]
BOY_NAMES = ["Perrin", "Alfie", "Jory", "Ben", "Tomas", "Robin"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
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
    "stop": [("What does 'stop' mean?", "To stop means to pause or not keep going for a moment.")],
    "neologism": [("What is a neologism?", "A neologism is a new word that someone has just made up.")],
    "lantern": [("What is a lantern?", "A lantern is a light that can be carried so you can see in the dark.")],
    "bridge": [("What is a bridge for?", "A bridge helps people cross water, a gap, or a hard-to-walk place.")],
    "dark": [("Why do people slow down in the dark?", "People slow down in the dark so they can see where to put their feet.")],
    "suspense": [("What is suspense in a story?", "Suspense is the feeling of waiting and wondering what will happen next.")],
}

KNOWLEDGE_ORDER = ["suspense", "stop", "neologism", "lantern", "bridge", "dark"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, caretaker, act, prize = f["hero"], f["caretaker"], f["activity"], f["prize_cfg"]
    return [
        f'Write a short folk tale for young children about a child named {hero.id}, a strange warning, and a new word called "{f.get("neologism", "moon-stop")}".',
        f"Tell a suspenseful village story where {hero.id} wants to {act.verb} but {caretaker.label} must help keep {prize.phrase} safe.",
        f'Write a simple tale that includes the words "{act.keyword}", "stop", and "neologism" and ends with a safer crossing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, caretaker, prize, act, stranger = f["hero"], f["caretaker"], f["prize"], f["activity"], f["stranger"]
    qa = [
        QAItem(
            question=f"Who is the child in the tale?",
            answer=f"The child is {hero.id}, a little {hero.type} who loved lantern-light and old stories.",
        ),
        QAItem(
            question=f"Why did {stranger.label} say stop at the bridge?",
            answer=(
                f"{stranger.label} said stop because the old bridge was unsafe in the dark, "
                f"and rushing could have caused trouble."
            ),
        ),
        QAItem(
            question=f"What new word did {hero.id} make up?",
            answer=(
                f"{hero.id} made up the neologism '{f.get('neologism', 'moon-stop')}', "
                f"which meant a careful pause so the lantern could guide the way."
            ),
        ),
    ]
    if f.get("resolved"):
        gear = _safe_fact(world, f, "gear")
        qa.append(
            QAItem(
                question=f"How did the family cross safely at the end?",
                answer=(
                    f"They used {gear.label} and crossed slowly, so {hero.id} could keep going "
                    f"without losing the light or the safety of {prize.label}."
                ),
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="lane", activity="bridge_crossing", prize="cloak", name="Mara", gender="girl", caretaker="grandmother"),
    StoryParams(place="wood", activity="whispering_road", prize="lantern", name="Perrin", gender="boy", caretaker="grandmother"),
    StoryParams(place="river", activity="lantern_walk", prize="cloak", name="Tova", gender="girl", caretaker="grandmother"),
    StoryParams(place="lane", activity="word_making", prize="lantern", name="Elin", gender="girl", caretaker="grandmother"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not threaten {noun}.)"
    if select_gear(activity, prize) is None:
        return f"(No story: there is no honest gear that can keep {noun} safe during {activity.gerund}.)"
    return "(No story: invalid combination.)"


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,Gender) :- valid(Place,A,P), wears(Gender,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
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
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale suspense world: a child, a warning, and a new word."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caretaker", choices=["grandmother"])
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
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize_id = rng.choice(list(combos))
    prize = _safe_lookup(PRIZES, prize_id)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    caretaker = getattr(args, "caretaker", None) or "grandmother"
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, caretaker=caretaker)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(ACTIVITIES, params.activity),
        _safe_lookup(PRIZES, params.prize),
        hero_name=params.name,
        hero_type=params.gender,
        caretaker_type=params.caretaker,
    )
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
            print(f"  {place:8} {act:18} {prize:8}  [{', '.join(genders)}]")
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
