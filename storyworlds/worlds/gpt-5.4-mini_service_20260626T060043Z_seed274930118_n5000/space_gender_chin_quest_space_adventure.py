#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/space_gender_chin_quest_space_adventure.py
===============================================================================================================

A small story world in the style of a space adventure:
a child dreams of a quest, a parent worries about safety,
and a sensible piece of gear makes the adventure possible.

The seed prompt suggests these ingredients:
- space
- gender
- chin
- quest
- style: Space Adventure

World premise:
A child wants to set off on a moonlit quest outside the ship, but the helmet
strap does not fit right under the chin. The parent refuses to launch them
until the gear is fixed. When the strap is adjusted, the child can go explore
safely.
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
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    g: object | None = None
    gear: object | None = None
    hero: object | None = None
    parent: object | None = None
    def __post_init__(self) -> None:
        for k in ("risk", "dust", "need", "workload"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "worry", "courage", "frustration", "love", "resolve"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str = "the space station"
    outdoors: bool = False
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
class Gear:
    id: str
    label: str
    phrase: str
    covers: set[str]
    fix: str
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


@dataclass
class StoryParams:
    place: str
    activity: str
    gear: str
    name: str
    gender: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


def _r_dust(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["dust"] < THRESHOLD:
            continue
        for item in list(world.entities.values()):
            if item.worn_by != actor.id or item.protective:
                continue
            if "chin" not in item.covers and item.covers != {"head", "chin"}:
                continue
            sig = ("dust", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dust"] += 1
            item.meters["risk"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} gear got dusty and unsafe.")
    return out


def _r_need(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["risk"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("need", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] += 1
        carer.meters["workload"] += 1
        out.append(f"That would mean more work for the parent.")
    return out


CAUSAL_RULES = [_r_dust, _r_need]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)


def place_detail(setting: Setting) -> str:
    if setting.place == "the space station":
        return "The corridor hummed softly, and the airlocks blinked like sleepy stars."
    if setting.place == "the moon dock":
        return "The moon dock was bright and silver, with little footprints already in the dust."
    return f"{setting.place.capitalize()} looked wide and ready for a quest."


def hero_intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "brave")
    world.say(
        f"{hero.id} was a little {trait} {hero.type} who loved stars, maps, and any grand quest."
    )


def love_space(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund} and listening to the ship's quiet space songs."
    )


def give_gear(world: World, parent: Entity, hero: Entity, gear: Gear) -> Entity:
    g = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        phrase=gear.phrase,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear.covers),
        plural=gear.plural,
    ))
    g.worn_by = hero.id
    return g


def predict_risk(world: World, hero: Entity, activity: Activity, gear: Gear) -> bool:
    sim = world.copy()
    sim.get(hero.id).meters["dust"] += 1
    for item in sim.entities.values():
        if item.worn_by == hero.id and item.protective and not gear.covers.issuperset(item.covers):
            pass
    return True


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, gear: Gear) -> None:
    hero.memes["need"] += 1
    world.say(
        f'"If we rush out now, your {gear.label} could slip under your chin and the dust would get in," '
        f"{parent.pronoun('possessive')} parent said."
    )
    world.say(f"{hero.id} looked down at the strap and frowned.")


def defy(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["frustration"] += 1
    hero.memes["courage"] += 1
    world.say(f"{hero.id} still wanted the quest and tried to {activity.rush}.")


def fix_gear(world: World, parent: Entity, hero: Entity, gear: Gear) -> Gear:
    hero.memes["resolve"] += 1
    world.say(
        f"{parent.pronoun('possessive').capitalize()} parent knelt down and tightened the strap so it sat right under {hero.pronoun('possessive')} chin."
    )
    world.say(
        f'"That feels better," {hero.id} said, touching {hero.pronoun('possessive')} chin and smiling.'
    )
    return gear


def resolve_story(world: World, hero: Entity, parent: Entity, activity: Activity, gear: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    world.say(
        f"{hero.id} nodded, and together they set off on the quest. "
        f"With {gear.label} snug under {hero.pronoun('possessive')} chin, {hero.id} could {activity.verb} safely."
    )
    world.say(
        f"By the end, the stars looked close, {hero.id} looked proud, and {parent.id} laughed as the little explorer marched into space."
    )


SETTINGS = {
    "station": Setting(place="the space station", outdoors=False, affords={"quest"}),
    "moon_dock": Setting(place="the moon dock", outdoors=True, affords={"quest"}),
}

ACTIVITIES = {
    "quest": Activity(
        id="quest",
        verb="go on the quest",
        gerund="going on quests",
        rush="dash down the airlock stairs",
        risk="dust and cold",
        zone={"chin", "head"},
        keyword="quest",
        tags={"space", "quest", "chin"},
    ),
}

GEAR = {
    "helmet": Gear(
        id="helmet",
        label="helmet",
        phrase="a bright helmet with a clear shield",
        covers={"head", "chin"},
        fix="strap",
        prep="check the helmet strap again",
        tail="walked out together toward the moon path",
    ),
}

GIRL_NAMES = ["Ada", "Luna", "Nova", "Mira", "Zara", "Ivy"]
BOY_NAMES = ["Orion", "Leo", "Kai", "Jules", "Eli", "Finn"]
TRAITS = ["curious", "brave", "gentle", "lively", "spirited"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for gear_id, gear in GEAR.items():
                if "chin" in gear.covers and act_id == "quest":
                    combos.append((place, act_id, gear_id))
    return combos


def explain_rejection(activity: Activity, gear: Gear) -> str:
    return (
        f"(No story: this quest needs gear that protects the chin, and this option does not. "
        f"Try the helmet.)"
    )


def explain_gender(gender: str) -> str:
    return f"(No story: this world can name either a girl or a boy hero, but not an unknown gender value {gender!r}.)"


def tell(setting: Setting, activity: Activity, gear_def: Gear,
         hero_name: str, hero_type: str, hero_traits: list[str], parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=hero_traits))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        phrase=gear_def.phrase,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear_def.covers),
    ))
    gear.worn_by = hero.id

    hero_intro(world, hero)
    love_space(world, hero, activity)
    world.say(f"{hero.id} wore {gear.phrase} for the big quest.")

    world.para()
    world.say(place_detail(setting))
    warn(world, parent, hero, activity, gear_def)
    defy(world, hero, activity)
    fix_gear(world, parent, hero, gear_def)

    world.para()
    resolve_story(world, hero, parent, activity, gear_def)

    world.facts.update(
        hero=hero,
        parent=parent,
        activity=activity,
        gear=gear_def,
        setting=setting,
        resolved=True,
    )
    return world


KNOWLEDGE = {
    "space": [
        (
            "What is space?",
            "Space is the huge area beyond Earth where the stars, planets, and moons are."
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a trip or mission to look for something, solve a problem, or reach a goal."
        )
    ],
    "chin": [
        (
            "What is a chin?",
            "Your chin is the part of your face below your mouth."
        )
    ],
    "helmet": [
        (
            "What does a helmet do?",
            "A helmet helps protect your head, and some helmets have a strap that keeps them steady."
        )
    ],
    "dust": [
        (
            "What is dust?",
            "Dust is made of tiny dry bits that can float, settle on things, and make them look dirty."
        )
    ],
}

KNOWLEDGE_ORDER = ["space", "quest", "chin", "helmet", "dust"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    activity = _safe_fact(world, f, "activity")
    return [
        f'Write a child-friendly space adventure about {hero.id} and a brave quest in space.',
        f"Tell a short story where a little {hero.type} wants to {activity.verb} but must fix the helmet under the chin first.",
        f'Write a gentle story that includes the word "quest" and ends with a safe trip into space.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, activity, gear = f["hero"], f["parent"], f["activity"], f["gear"]
    qa = [
        QAItem(
            question=f"Who wanted to go on the quest?",
            answer=f"{hero.id} wanted to go on the quest and explore the space path."
        ),
        QAItem(
            question=f"What worried {parent.id} about the quest?",
            answer=f"{parent.id} worried that the helmet strap would slip under {hero.pronoun('possessive')} chin and let in dust."
        ),
        QAItem(
            question=f"What did they do so {hero.id} could go safely?",
            answer=f"They tightened the helmet strap so the helmet sat right under {hero.pronoun('possessive')} chin."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} going on the quest happily and safely, with the helmet snug and the stars ahead."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.covers:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
wants_quest(hero).
chin_risk(hero) :- wears(hero, helmet), covers(helmet, chin).
good_story(hero) :- wants_quest(hero), chin_risk(hero), has_fix(helmet).

has_fix(helmet) :- gear(helmet), covers(helmet, chin).
valid(Place, quest, helmet) :- setting(Place), affords(Place, quest), gear(helmet), has_fix(helmet), covers(helmet, chin).
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
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", gid, c))
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
    ap = argparse.ArgumentParser(description="Space Adventure story world: a quest, a chin strap, and a safe launch.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if getattr(args, "gender", None) and getattr(args, "gender", None) not in {"girl", "boy"}:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
        and (getattr(args, "gear", None) is None or c[2] == getattr(args, "gear", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, gear = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, gear=gear, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(ACTIVITIES, params.activity),
        GEAR[params.gear],
        params.name,
        params.gender,
        [params.trait, "stubborn"],
        params.parent,
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


CURATED = [
    StoryParams(place="station", activity="quest", gear="helmet", name="Nova", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="moon_dock", activity="quest", gear="helmet", name="Orion", gender="boy", parent="father", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp

        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, act, gear in combos:
            print(f"  {place:10} {act:8} {gear:8}")
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
            header = f"### {p.name}: {p.activity} at {p.place} (gear: {p.gear})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
