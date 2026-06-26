#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/honey_dirty_transformation_tall_tale.py
==============================================================================================================

A small standalone story world for a tall-tale about honey, dirt, and a
surprising transformation.

Premise:
- A child or grown-up sized hero is carrying honey through a messy place.
- Dirty hands or a dirty cloth threaten to spoil the sweet work.
- A wise helper suggests a simple transformation: wash, warm, and twist the
  mess into something bright and useful.

The world is intentionally tiny and constraint-checked.  It generates one
complete story with a clear beginning, a turning point, and an ending image.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    honey: object | None = None
    target: object | None = None
    def __post_init__(self) -> None:
        for k in ("dirty", "honeyed", "clean", "warm", "bright"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "worry", "pride", "wonder", "determination", "calm"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
    place: str
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
class Transformation:
    id: str
    label: str
    source: str
    result: str
    prep: str
    finish: str
    needed_mess: str
    needed_region: str
    glow: str
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _tall_honey_glow(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["honeyed"] < THRESHOLD or actor.meters["dirty"] < THRESHOLD:
            continue
        sig = ("transformation", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["bright"] += 1
        actor.meters["dirty"] = max(0.0, actor.meters["dirty"] - 1)
        actor.memes["wonder"] += 1
        out.append("__transformation__")
    return out


def _cleaning_brightens(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["dirty"] < THRESHOLD:
            continue
        sig = ("clean", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        item.meters["dirty"] = 0.0
        item.meters["clean"] += 1
        item.meters["bright"] += 1
        out.append(f"The dirt gave way, and {item.label} came out clean.")
    return out


CAUSAL_RULES = [_tall_honey_glow, _cleaning_brightens]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__transformation__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def predict_outcome(world: World, actor: Entity, activity: Activity, target_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    target = sim.entities.get(target_id)
    return {
        "dirty": bool(target and target.meters["dirty"] >= THRESHOLD),
        "bright": bool(target and target.meters["bright"] >= THRESHOLD),
    }


def intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "bold")
    world.say(
        f"{hero.id} was a little {trait} {hero.type} who could carry a jar of honey "
        f"as if it were a moon in a lunch pail."
    )


def loves_honey(world: World, hero: Entity, honey: Entity) -> None:
    hero.memes["love"] += 1
    world.say(
        f"{hero.id} loved {honey.label}, and {hero.pronoun('possessive')} eyes went round "
        f"whenever the golden stuff shone."
    )


def arrives(world: World, hero: Entity, helper: Entity) -> None:
    day = "One sunny afternoon, "
    world.say(
        f"{day}{hero.id} and {helper.label} came to {world.setting.place}."
    )
    world.say(
        f"The place was busy with sweet smells, sticky spots, and enough dust to dust a wagon."
    )


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["determination"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb}, but the path was already dirty and rough."
    )


def warn(world: World, helper: Entity, hero: Entity, activity: Activity, target: Entity) -> bool:
    pred = predict_outcome(world, hero, activity, target.id)
    if not pred["dirty"]:
        return False
    world.facts["predicted_brightness"] = pred["bright"]
    world.say(
        f'"If you rush in now," {helper.label} said, "your {target.label} will get '
        f'{activity.soil}."'
    )
    return True


def messy_step(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} leaned forward anyway and tried to {activity.rush}."
    )


def helper_turn(world: World, helper: Entity, hero: Entity, transform: Transformation) -> None:
    helper.memes["calm"] += 1
    world.say(
        f"Then {helper.label} smiled a tall-tale smile and said, "
        f'"Let us {transform.prep}."'
    )


def perform_transformation(world: World, hero: Entity, source: Entity, transform: Transformation) -> None:
    source.meters["dirty"] = max(0.0, source.meters["dirty"] - 1)
    source.meters["honeyed"] += 1
    source.meters["bright"] += 1
    hero.memes["wonder"] += 1
    world.say(
        f"They did {transform.finish}, and the old {source.label} changed from {transform.source} "
        f"to {transform.result}."
    )


def resolution(world: World, hero: Entity, helper: Entity, target: Entity, transform: Transformation) -> None:
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"By the time the last drop of honey gleamed, {hero.id} was laughing, "
        f"{target.label} was {transform.glow}, and {helper.label} was proud as a barn owl."
    )


def tell(setting: Setting, activity: Activity, transform: Transformation,
         hero_name: str = "Milo", hero_type: str = "boy",
         hero_traits: Optional[list[str]] = None, helper_type: str = "grandmother") -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type,
                            traits=["little"] + (hero_traits or ["brave", "curious"])))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="his grandmother"))
    honey = world.add(Entity(id="honey", type="thing", label="jar of honey", phrase="a jar of honey"))
    target = world.add(Entity(id="target", type="thing", label=transform.label, phrase=transform.label))
    target.meters["dirty"] = 1.0

    intro(world, hero)
    loves_honey(world, hero, honey)
    world.para()
    arrives(world, hero, helper)
    wants(world, hero, activity)
    warn(world, helper, hero, activity, target)
    messy_step(world, hero, activity)
    world.para()
    helper_turn(world, helper, hero, transform)
    perform_transformation(world, hero, target, transform)
    resolution(world, hero, helper, target, transform)

    world.facts.update(hero=hero, helper=helper, honey=honey, target=target,
                       activity=activity, transform=transform, setting=setting)
    return world


SETTINGS = {
    "porch": Setting(place="the porch", indoor=False, affords={"honey_walk"}),
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"honey_walk"}),
    "barn": Setting(place="the barn", indoor=False, affords={"honey_walk"}),
}

ACTIVITIES = {
    "honey_walk": Activity(
        id="honey_walk",
        verb="carry the honey to the table",
        gerund="carrying honey",
        rush="dash toward the table with the jar",
        mess="dirty",
        soil="dirty and sticky",
        zone={"hands"},
        weather="sunny",
        keyword="honey",
        tags={"honey", "dirty"},
    ),
}

TRANSFORMATIONS = {
    "lantern": Transformation(
        id="lantern",
        label="old tin lantern",
        source="muddy and dull",
        result="a golden honey lantern",
        prep="warm the jar, wipe the dirt away, and paint the tin with honeylight",
        finish="warming, wiping, and turning",
        needed_mess="dirty",
        needed_region="hands",
        glow="glowing like a sunrise in a jar",
    ),
    "windmill": Transformation(
        id="windmill",
        label="small wooden windmill",
        source="dusty and gray",
        result="a bright honey-gold windmill",
        prep="spin the blades, smooth the dust, and glaze it with honey",
        finish="spinning, smoothing, and glazing",
        needed_mess="dirty",
        needed_region="hands",
        glow="shining like a brass song",
    ),
}

NAMES = ["Milo", "Nell", "Ruby", "Otto", "Pip", "June"]
TRAITS = ["bold", "curious", "cheerful", "stubborn", "lively"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for tr_id in TRANSFORMATIONS:
                out.append((place, act_id, tr_id))
    return out


@dataclass
class StoryParams:
    place: str
    activity: str
    transformation: str
    name: str
    gender: str
    helper: str
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
    hero = _safe_fact(world, f, "hero")
    activity = _safe_fact(world, f, "activity")
    transform = _safe_fact(world, f, "transform")
    return [
        f'Write a short tall tale for a child about {hero.id} and honey, with a dirty problem and a bright transformation.',
        f"Tell a playful story where {hero.id} wants to {activity.verb} and then turns a dirty thing into {transform.result}.",
        f'Write a gentle tall tale that includes the words "honey" and "dirty" and ends with a shining transformation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    target = _safe_fact(world, f, "target")
    activity = _safe_fact(world, f, "activity")
    transform = _safe_fact(world, f, "transform")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little {hero.type}, and {helper.label}, who helped with the honey and the dirt.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {activity.verb}, even though the path was dirty.",
        ),
        QAItem(
            question=f"What changed during the transformation?",
            answer=f"The {target.label} changed from {transform.source} to {transform.result}.",
        ),
        QAItem(
            question=f"Why did the helper worry?",
            answer=f"{helper.label} worried because the honey work would make the {target.label} dirty and sticky.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {target.label} {transform.glow} and {hero.id} feeling proud and happy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is honey?",
            answer="Honey is a sweet, sticky food made by bees and stored in combs or jars.",
        ),
        QAItem(
            question="Why can dirt be a problem?",
            answer="Dirt can make things grimy or sticky, and some things need to stay clean to look nice or work well.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form or state into another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="porch", activity="honey_walk", transformation="lantern",
                name="Milo", gender="boy", helper="grandmother", trait="brave"),
    StoryParams(place="kitchen", activity="honey_walk", transformation="windmill",
                name="June", gender="girl", helper="grandmother", trait="curious"),
]


def explain_rejection() -> str:
    return "(No story: this tiny world only supports honey work that can lead to a dirty-to-bright transformation.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale story world: honey, dirty, transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["grandmother", "grandfather"])
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
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "activity", None):
        combos = [c for c in combos if c[1] == getattr(args, "activity", None)]
    if getattr(args, "transformation", None):
        combos = [c for c in combos if c[2] == getattr(args, "transformation", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, act, tr = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    helper = getattr(args, "helper", None) or "grandmother"
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=act, transformation=tr, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(TRANSFORMATIONS, params.transformation),
                 hero_name=params.name, hero_type="girl" if params.gender == "girl" else "boy",
                 hero_traits=[params.trait], helper_type=params.helper)
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
at_risk(A,T) :- activity(A), transformation(T), needed_mess(T,M), mess_of(A,M), needed_region(T,R), splashes(A,R).
valid_story(P,A,T) :- place(P), affords(P,A), at_risk(A,T), has_fix(A,T).
has_fix(A,T) :- needed_mess(T,M), guards(G,M), needed_region(T,R), covers(G,R).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for tid, t in TRANSFORMATIONS.items():
        lines.append(asp.fact("transformation", tid))
        lines.append(asp.fact("needed_mess", tid, t.needed_mess))
        lines.append(asp.fact("needed_region", tid, t.needed_region))
    lines.append(asp.fact("guards", "helper_hands", "dirty"))
    lines.append(asp.fact("covers", "helper_hands", "hands"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_combos())
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid_story/3."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.name}: {p.activity} at {p.place} (transformation: {p.transformation})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
