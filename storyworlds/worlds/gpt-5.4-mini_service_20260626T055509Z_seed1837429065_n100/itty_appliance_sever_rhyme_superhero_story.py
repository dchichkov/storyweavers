#!/usr/bin/env python3
"""
storyworlds/worlds/itty_appliance_sever_rhyme_superhero_story.py
================================================================

A small superhero-style story world about an itty hero, an appliance, and a
careful warning that something might sever. The stories are built from a tiny
simulated model with physical meters and emotional memes, and they include
rhyming lines so the style feels like a comic-book chant.

Seed tale sketch:
---
An itty superhero loved a humming appliance because it made the room feel lively.
But the appliance had a moving part and a loose ribbon nearby could sever.
The hero wanted to help right away, while the grown-up worried and called for a
safer plan. In the end, the hero used a better setup so the appliance could run
and the ribbon stayed safe.

Narration goals:
- superhero flavor: cape, zoom, rescue, brave helper
- rhyme flavor: short repeated rhyming beats and a sing-song ending
- state-driven: the appliance, ribbon, and hero mood determine the plot
- strict reasonableness: only stories with a real risk and a real fix are allowed
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    gear: object | None = None
    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    def _m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def _e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    place: str
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
    keyword: str
    rhyme: str
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_risk(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("danger", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("risk", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["sever_risk"] = item.meters.get("sever_risk", 0.0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} could get severed.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters.get("sever_risk", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] = carer.memes.get("worry", 0.0) + 1
        out.append(f"That would make {carer.label} worry.")
    return out


CAUSAL_RULES = [_r_risk, _r_worry]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def rhyme_line(activity: Activity, hero: Entity) -> str:
    return f"Zip-zip, {hero.id}, with a quick little spin; {activity.rhyme}"


def predict_risk(world: World, hero: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(hero.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "risky": prize.meters.get("sever_risk", 0.0) >= THRESHOLD,
        "worry": sim.get("Parent").memes.get("worry", 0.0),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters["danger"] = actor.meters.get("danger", 0.0) + 1
    actor.memes["gumption"] = actor.memes.get("gumption", 0.0) + 1
    propagate(world, narrate=narrate)


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Pip", hero_type: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        label=hero_name, meters={"danger": 0.0}, memes={"brave": 1.0}
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="Ribbon", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural
    ))
    world.add(Entity(id="Appliance", type="appliance", label="the appliance"))
    world.add(Entity(id="RibbonGuard", type="gear", label="a ribbon guard", protective=True, covers={"torso"}))

    hero.say = None  # harmless attribute placeholder; not used

    world.say(
        f"{hero.id} was an itty superhero with a bright cape and a grin that could outshine noon."
    )
    world.say(
        f"{hero.id} loved the humming appliance because it puffed the room alive like a drum."
    )
    world.say(rhyme_line(activity, hero))
    world.say(
        f"One day, {hero.id} and {hero.pronoun('possessive')} {parent_type} went to {setting.place}."
    )
    world.say(
        f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} {parent_type} noticed {prize.label} nearby."
    )

    world.para()
    pred = predict_risk(world, hero, activity, prize.id)
    if pred["risky"]:
        world.facts["predicted_risk"] = True
        world.facts["predicted_worry"] = pred["worry"]
        world.say(
            f'"If you do that, your {prize.label} could get {activity.soil}," {parent_type} said.'
        )
    else:
        world.facts["predicted_risk"] = False

    hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 1
    world.say(
        f"{hero.id} wanted to zoom ahead anyway, but then {hero.id} saw the loose edge by the machine."
    )
    world.say(
        f"{hero.id} tried to {activity.rush}, and the room felt tense as a thundercloud."
    )

    world.para()
    hero.memes["shared"] = hero.memes.get("shared", 0.0) + 1
    world.say(
        f"{parent_type.capitalize()} pointed to a safer plan: first, {activity.keyword} far from the edge."
    )
    gear_def = None
    if pred["risky"]:
        gear_def = select_gear(activity, prize)
        if gear_def:
            gear = world.add(Entity(
                id=gear_def.id, type="gear", label=gear_def.label,
                protective=True, covers=set(gear_def.covers), plural=gear_def.plural,
                owner=hero.id, caretaker=parent.id
            ))
            gear.worn_by = hero.id
            world.say(
                f"{hero.id} put on {gear.label} and felt ready to rescue the day."
            )
            world.say(
                f'"How about we {gear_def.prep}?" {parent_type} asked. "{activity.rhyme}"'
            )
    if gear_def is None and pred["risky"]:
        pass

    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    if gear_def:
        world.say(
            f"{hero.id} nodded fast, and together they {gear_def.tail}."
        )
        world.say(
            f"Then {hero.id} was {activity.gerund}, and {prize.label} stayed safe and neat."
        )
    else:
        world.say(
            f"{hero.id} nodded fast, and together they chose the safer distance."
        )
        world.say(
            f"Then {hero.id} was {activity.gerund}, and {prize.label} stayed safe and neat."
        )
    world.say(
        f"Zip and zap, the little hero won the day; the {activity.keyword} stayed steady, and the trouble flew away."
    )

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear_def,
        resolved=True,
    )
    return world


SETTINGS = {
    "workshop": Setting(place="the workshop", affords={"fan", "vacuum", "dryer"}),
    "kitchen": Setting(place="the kitchen", affords={"mixer", "fan", "dryer"}),
    "laundry": Setting(place="the laundry room", affords={"dryer", "fan"}),
}

ACTIVITIES = {
    "fan": Activity(
        id="fan",
        verb="help the fan spin",
        gerund="helping the fan spin",
        rush="dash close to the fan",
        mess="windy",
        soil="ruffled",
        zone={"torso"},
        keyword="fan",
        rhyme="Bam-bam, no jam; keep the ribbon back and the air will wham.",
        tags={"fan", "safe"},
    ),
    "vacuum": Activity(
        id="vacuum",
        verb="run the vacuum",
        gerund="running the vacuum",
        rush="race near the vacuum",
        mess="dusty",
        soil="dusty",
        zone={"torso"},
        keyword="vacuum",
        rhyme="Zoom-zoom, room-to-room; keep the loose ribbon clear, and the dust says swoon.",
        tags={"vacuum", "dust"},
    ),
    "dryer": Activity(
        id="dryer",
        verb="use the dryer",
        gerund="using the dryer",
        rush="rush to the dryer",
        mess="hot",
        soil="singed",
        zone={"torso"},
        keyword="dryer",
        rhyme="Whirr-whirr, little blur; stay back from the vent, and the cape will purr.",
        tags={"dryer", "heat"},
    ),
    "mixer": Activity(
        id="mixer",
        verb="mix the batter",
        gerund="mixing the batter",
        rush="lean over the mixer",
        mess="splashy",
        soil="splattered",
        zone={"torso"},
        keyword="mixer",
        rhyme="Mix-mix, quick quick fix; keep the ribbon high, and the batter won't stick.",
        tags={"mixer", "splash"},
    ),
}

PRIZES = {
    "cape": Prize(label="cape", phrase="a bright red cape", type="cape", region="torso"),
    "ribbon": Prize(label="ribbon", phrase="a shiny ribbon", type="ribbon", region="torso"),
    "banner": Prize(label="banner", phrase="a tiny parade banner", type="banner", region="torso", plural=False),
}

GEAR = [
    Gear(
        id="clip",
        label="a cape clip",
        covers={"torso"},
        guards={"windy", "dusty", "hot", "splashy"},
        prep="clip down the cape and stand back",
        tail="clipped the cape and stood back",
    ),
    Gear(
        id="cover",
        label="a clear cover",
        covers={"torso"},
        guards={"dusty", "splashy"},
        prep="cover the ribbon and keep it tidy",
        tail="covered the ribbon and kept it tidy",
    ),
    Gear(
        id="mitt",
        label="a super mitt",
        covers={"torso"},
        guards={"hot"},
        prep="put on a super mitt first",
        tail="put on the super mitt and chose a safe spot",
    ),
]

HERO_NAMES = ["Pip", "Nia", "Bo", "Zia", "Rae", "Milo"]
PARENTS = ["mother", "father"]
TRAITS = ["itty", "brave", "bright", "quick"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


KNOWLEDGE = {
    "fan": [("What does a fan do?", "A fan moves air around so a room can feel cooler or fresher.")],
    "vacuum": [("What does a vacuum do?", "A vacuum sucks up dust and crumbs from the floor.")],
    "dryer": [("What does a dryer do?", "A dryer blows warm air to help wet clothes become dry.")],
    "mixer": [("What does a mixer do?", "A mixer stirs or beats ingredients together for cooking.")],
    "cape": [("What is a cape?", "A cape is a flowing piece of clothing that often makes a superhero look heroic.")],
    "ribbon": [("What is a ribbon?", "A ribbon is a thin strip of cloth that can be tied or used to decorate things.")],
}

KNOWLEDGE_ORDER = ["fan", "vacuum", "dryer", "mixer", "cape", "ribbon"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short superhero story for a child about an itty hero named {hero.id} and a {act.keyword}.',
        f"Tell a rhyming story where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} {parent.type} worries about {prize.label}.",
        f'Write a tiny comic-style tale that includes the word "{hero.id}" and ends with a safe, happy rescue.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    qa = [
        QAItem(
            question=f"Who is the itty superhero in the story?",
            answer=f"The itty superhero is {hero.id}, who wears a cape and tries to help with the {act.keyword}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the {act.keyword}?",
            answer=f"{hero.id} wanted to {act.verb}, which sounded fun but needed a safer plan.",
        ),
        QAItem(
            question=f"Why did {parent.type} worry about {prize.label}?",
            answer=f"{parent.type.capitalize()} worried because the {act.keyword} could leave the {prize.label} {act.soil}.",
        ),
    ]
    if f.get("resolved"):
        gear = _safe_fact(world, f, "gear")
        qa.append(
            QAItem(
                question=f"How did the hero keep the {prize.label} safe?",
                answer=f"They used {gear.label} first, so the {act.keyword} could happen without hurting the {prize.label}.",
            )
        )
        qa.append(
            QAItem(
                question=f"How did the story end?",
                answer=f"It ended with {hero.id} feeling proud, the {prize.label} staying safe, and a rhyming rescue beat.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    if f.get("prize"):
        tags.add(f["prize"].label)
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="workshop", activity="fan", prize="cape", name="Pip", parent="mother", trait="itty"),
    StoryParams(place="kitchen", activity="mixer", prize="ribbon", name="Nia", parent="father", trait="bright"),
    StoryParams(place="laundry", activity="dryer", prize="banner", name="Rae", parent="mother", trait="brave"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} does not put the {prize.label} at honest risk, "
        f"so the warning would not feel real. The story needs a true superhero problem and a true fix.)"
    )


def explain_gender(_: str, __: str) -> str:
    return "(No story: this world does not use gendered prize restrictions.)"


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
fix(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), fix(_, A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        if pr.plural:
            lines.append(asp.fact("prize_plural", pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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
    ap = argparse.ArgumentParser(description="Superhero rhyme story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENTS)
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = rng.choice(list(combos))
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        name=getattr(args, "name", None) or rng.choice(HERO_NAMES),
        parent=getattr(args, "parent", None) or rng.choice(PARENTS),
        trait="itty",
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize),
                 params.name, "girl", params.parent)
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, prize) combos:\n")
        for place, act, prize in triples:
            print(f"  {place:10} {act:8} {prize:8}")
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
