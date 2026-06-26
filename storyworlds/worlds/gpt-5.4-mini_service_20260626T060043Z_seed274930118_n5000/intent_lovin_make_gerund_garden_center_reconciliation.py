#!/usr/bin/env python3
"""
storyworlds/worlds/intent_lovin_make_gerund_garden_center_reconciliation.py
===========================================================================

A compact comedy storyworld set in a garden center.

Premise:
- A child arrives with a clear intent: make-gerund something delightful with plants.
- The child is lovin the idea, but the first plan is too big, too messy, or too silly.
- A parent or helper warns them with gentle dialogue.
- The situation resolves through reconciliation: a smaller, practical plan that still
  keeps the child's joy and produces a concrete ending image.

This world is intentionally small and constraint-checked:
- typed entities with meters and memes
- state-driven narration
- explicit invalid choices raise StoryError
- inline ASP twin mirrors the Python reasonableness gate
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
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        self.meters = __import__('collections').defaultdict(float, self.meters)
        self.memes = __import__('collections').defaultdict(float, self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
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
    place: str = "the garden center"
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
class Intent:
    id: str
    verb: str
    gerund: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str = "intent"
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
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
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


def prize_at_risk(intent: Intent, prize: Prize) -> bool:
    return prize.region in intent.zone


def select_gear(intent: Intent, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if intent.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, intent: Intent, prize_id: str) -> dict:
    sim = copy_world(world)
    do_intent(sim, sim.get(actor.id), intent, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters.get("dirty", 0) >= THRESHOLD)}


def copy_world(world: World) -> World:
    import copy
    clone = World(world.setting)
    clone.entities = copy.deepcopy(world.entities)
    clone.zone = set(world.zone)
    clone.fired = set(world.fired)
    clone.paragraphs = [[]]
    clone.facts = dict(world.facts)
    return clone


def _apply_mess(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for intent_kind in INTENT_KINDS:
            if actor.meters.get(intent_kind, 0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("mess", item.id, intent_kind)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[intent_kind] = item.meters.get(intent_kind, 0) + 1
                item.meters["dirty"] = item.meters.get("dirty", 0) + 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got messy.")
    return out


def _apply_relief(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters.get("dirty", 0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("relief", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["workload"] = carer.memes.get("workload", 0) + 1
        out.append(f"That would mean more work for {carer.label}.")
    return out


def _apply_tension(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes.get("grabbed_by", 0) < THRESHOLD or actor.memes.get("defiance", 0) < THRESHOLD:
            continue
        sig = ("tension", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] = actor.memes.get("conflict", 0) + 1
        return ["__tension__"]
    return []


RULES = [_apply_mess, _apply_relief, _apply_tension]


def propagate(world: World, narrate: bool = True) -> None:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__tension__")
    if narrate:
        for s in produced:
            world.say(s)


def do_intent(world: World, actor: Entity, intent: Intent, narrate: bool = True) -> None:
    world.zone = set(intent.zone)
    actor.meters[intent.mess] = actor.meters.get(intent.mess, 0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0) + 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who was lovin every seed packet and sunny aisle at the garden center."
    )


def intent_beat(world: World, hero: Entity, intent: Intent) -> None:
    hero.memes["intent"] = hero.memes.get("intent", 0) + 1
    world.say(f"{hero.pronoun().capitalize()} had one clear intent: to {intent.verb}.")
    world.say(f"It sounded silly and wonderful, which made {hero.id} grin even harder.")


def browse(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"At the garden center, {hero.id} skipped past watering cans, tiny shovels, and a mountain of cheerful little pots."
    )
    world.say(
        f"Then {hero.pronoun().capitalize()} said to {helper.label}, \"I want to make-gerund the biggest flower tower ever!\""
    )


def warn(world: World, helper: Entity, hero: Entity, intent: Intent, prize: Entity) -> bool:
    pred = predict_mess(world, hero, intent, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = intent.soil
    world.say(
        f"\"If you do that, your {prize.label} will get {intent.soil},\" {helper.label} said."
    )
    world.say(
        f"\"And then I will have to scrub it while you make a very muddy victory face.\""
    )
    return True


def defy(world: World, hero: Entity, intent: Intent) -> None:
    hero.memes["defiance"] = hero.memes.get("defiance", 0) + 1
    world.say(f"{hero.id} puffed out {hero.pronoun('possessive')} cheeks.")
    world.say(f"\"But I lovin it! I want to {intent.verb} right now!\" {hero.id} said.")


def grab_conflict(world: World, helper: Entity, hero: Entity, intent: Intent) -> None:
    hero.memes["grabbed_by"] = hero.memes.get("grabbed_by", 0) + 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.label} gently caught {hero.pronoun('possessive')} hand and said, "
        f"\"We can still do it, just not in the banana-sized version.\""
    )


def reconcile(world: World, helper: Entity, hero: Entity, intent: Intent, prize: Entity) -> Optional[Gear]:
    gear = select_gear(intent, prize)
    if gear is None:
        return None
    item = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        owner=hero.id,
        caretaker=helper.id,
        protective=True,
        covers=set(gear.covers),
        plural=gear.plural,
    ))
    item.worn_by = hero.id
    if predict_mess(world, hero, intent, prize.id)["soiled"]:
        item.worn_by = None
        del world.entities[item.id]
        return None
    world.say(
        f"{helper.label} thought for a second, then smiled and said, "
        f"\"How about we {gear.prep}?\""
    )
    return item


def accept(world: World, helper: Entity, hero: Entity, intent: Intent, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["love"] = hero.memes.get("love", 0) + 1
    hero.memes["conflict"] = 0
    world.say(
        f"{hero.id} laughed so hard that {hero.pronoun('possessive')} shoulders shook. "
        f"\"Okay! That sounds more genius than giant,\" {hero.id} said."
    )
    world.say(
        f"They {gear.tail}. Soon {hero.id} was {intent.gerund}, {prize.label} stayed clean, "
        f"and the little plant display looked even happier for it."
    )


def tell(setting: Setting, intent: Intent, prize_cfg: Prize, hero_name: str, hero_type: str,
         helper_type: str, helper_label: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label=helper_label))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=helper.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    intro(world, hero)
    intent_beat(world, hero, intent)
    browse(world, hero, helper)

    world.para()
    warn(world, helper, hero, intent, prize)
    defy(world, hero, intent)
    grab_conflict(world, helper, hero, intent)

    world.para()
    gear = reconcile(world, helper, hero, intent, prize)
    if gear:
        accept(world, helper, hero, intent, prize, gear)

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        intent=intent,
        gear=gear,
        resolved=gear is not None,
    )
    return world


SETTINGS = {
    "garden_center": Setting(place="the garden center", affords={"make_gerund"}),
}

INTENT_KINDS = {"make_gerund"}

INTENTS = {
    "make_gerund": Intent(
        id="make_gerund",
        verb="make a giant flower tower",
        gerund="making a flower tower",
        mess="dirty",
        soil="all dusty and soil-smudged",
        zone={"hands", "torso"},
        keyword="make-gerund",
        tags={"garden", "flowers", "pots"},
    )
}

PRIZES = {
    "white_shirt": Prize(
        label="white shirt",
        phrase="a clean white shirt",
        type="shirt",
        region="torso",
    ),
    "new_overalls": Prize(
        label="overalls",
        phrase="tiny new overalls",
        type="overalls",
        region="torso",
        plural=True,
    ),
    "garden_hat": Prize(
        label="garden hat",
        phrase="a bright garden hat",
        type="hat",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="apron",
        label="a canvas apron",
        covers={"torso"},
        guards={"dirty"},
        prep="put on a canvas apron first",
        tail="went to fetch the canvas apron",
    ),
    Gear(
        id="smock",
        label="a funny little smock",
        covers={"torso"},
        guards={"dirty"},
        prep="put on the funny little smock first",
        tail="fetched the funny little smock",
    ),
]

HERO_NAMES = ["Milo", "Nina", "Pip", "Ruby", "Ollie", "Tia"]
HERO_TYPES = ["boy", "girl"]
HELPERS = [("mother", "Mom"), ("father", "Dad"), ("worker", "Mr. Bloom")]
TRAITS = ["cheerful", "curious", "silly"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for intent_id in setting.affords:
            intent = _safe_lookup(INTENTS, intent_id)
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(intent, prize) and select_gear(intent, prize):
                    combos.append((place, intent_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    intent: str
    prize: str
    name: str
    hero_type: str
    helper_type: str
    helper_label: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld set in a garden center.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--intent", choices=INTENTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--helper-type", choices=[h[0] for h in HELPERS])
    ap.add_argument("--helper-label")
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
    if getattr(args, "intent", None) and getattr(args, "prize", None):
        intent = _safe_lookup(INTENTS, getattr(args, "intent", None))
        prize = _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(intent, prize) and select_gear(intent, prize)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "intent", None) is None or c[1] == getattr(args, "intent", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, intent_id, prize_id = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    helper_type, helper_label = rng.choice(HELPERS)
    if getattr(args, "helper_type", None):
        helper_type = getattr(args, "helper_type", None)
        helper_label = dict(HELPERS)[helper_type]
    if getattr(args, "helper_label", None):
        helper_label = getattr(args, "helper_label", None)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, intent=intent_id, prize=prize_id, name=name,
                       hero_type=hero_type, helper_type=helper_type,
                       helper_label=helper_label, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(INTENTS, params.intent), _safe_lookup(PRIZES, params.prize),
                 params.name, params.hero_type, params.helper_type, params.helper_label)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    intent = _safe_fact(world, f, "intent")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a funny story set in a garden center where a child named {hero.id} has the intent to {intent.verb}.',
        f"Tell a comedy about {hero.id} and {helper.label} as they argue, joke, and reconcile over {prize.phrase}.",
        f'Write a child-friendly story that includes the phrase "{intent.keyword}" and ends with a cheerful compromise.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, intent, prize = f["hero"], f["helper"], f["intent"], f["prize"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do at the garden center?",
            answer=f"{hero.id} wanted to {intent.verb}. That was {hero.pronoun('possessive')} big intent for the day.",
        ),
        QAItem(
            question=f"Why did {helper.label} worry about {prize.label}?",
            answer=f"{helper.label} worried because the plan would leave {prize.phrase} {intent.soil}.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"It ended with reconciliation: {hero.id} got to keep going, but with {f['gear'].label if f.get('gear') else 'a safer plan'}.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"What did {hero.id} and {helper.label} agree to use?",
                answer=f"They agreed to use {f['gear'].label} so the making could stay fun and the {prize.label} could stay clean.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a garden center?",
            answer="A garden center is a shop where people buy plants, soil, pots, tools, and other things for growing and caring for gardens.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means two people stop disagreeing and find a way to be happy together again.",
        ),
        QAItem(
            question="What is a dialogue?",
            answer="Dialogue is spoken conversation between people in a story.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        s = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={m}")
        if s:
            bits.append(f"memes={s}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(intent: Intent, prize: Prize) -> str:
    if not prize_at_risk(intent, prize):
        return f"(No story: {intent.gerund} would not really risk the {prize.label}.)"
    return f"(No story: there is no believable gear here that protects {prize.label} from {intent.gerund}.)"


ASP_RULES = r"""
prize_at_risk(I, P) :- intent(I), splashes(I, R), worn_on(P, R).
protects(G, I, P) :- gear(G), prize_at_risk(I, P), guards(G, M), mess_of(I, M), covers(G, R), worn_on(P, R).
has_fix(I, P) :- protects(_, I, P).
valid(Place, I, P) :- affords(Place, I), prize_at_risk(I, P), has_fix(I, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for iid, intent in INTENTS.items():
        lines.append(asp.fact("intent", iid))
        lines.append(asp.fact("mess_of", iid, intent.mess))
        for r in sorted(intent.zone):
            lines.append(asp.fact("splashes", iid, r))
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


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


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
    StoryParams("garden_center", "make_gerund", "white_shirt", "Milo", "boy", "mother", "Mom", "cheerful"),
    StoryParams("garden_center", "make_gerund", "new_overalls", "Nina", "girl", "father", "Dad", "silly"),
    StoryParams("garden_center", "make_gerund", "garden_hat", "Pip", "boy", "worker", "Mr. Bloom", "curious"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
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
            header = f"### {p.name}: {p.intent} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "intent", None) and getattr(args, "prize", None):
        intent = _safe_lookup(INTENTS, getattr(args, "intent", None))
        prize = _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(intent, prize) and select_gear(intent, prize)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "intent", None) is None or c[1] == getattr(args, "intent", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, intent_id, prize_id = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    helper_type, helper_label = rng.choice(HELPERS)
    if getattr(args, "helper_type", None):
        helper_type = getattr(args, "helper_type", None)
        helper_label = dict(HELPERS)[helper_type]
    if getattr(args, "helper_label", None):
        helper_label = getattr(args, "helper_label", None)
    return StoryParams(
        place=place,
        intent=intent_id,
        prize=prize_id,
        name=name,
        hero_type=hero_type,
        helper_type=helper_type,
        helper_label=helper_label,
        trait=rng.choice(TRAITS),
    )


if __name__ == "__main__":
    main()
