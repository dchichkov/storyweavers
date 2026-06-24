#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/mumps_crouton_inner_monologue_superhero_story.py
=================================================================================================

A small, standalone story world for a superhero-style tale with inner monologue,
built from the seed words: mumps, crouton.

Core premise:
- A young superhero wants to keep helping people.
- He gets mumps, which makes loud hero work a bad idea.
- He also has a crunchy crouton treat that helps make resting feel like a
  mission instead of a punishment.
- The story turns on inner monologue, worry, and a kind compromise.

This script follows the Storyweavers contract:
- stdlib-only prose engine
- shared StoryError / StorySample / QAItem imported eagerly
- inline ASP twin plus Python reasonableness gate
- deterministic story generation from params
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    parent: object | None = None
    sickness: object | None = None
    snack: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    risk: str
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
class Comfort:
    id: str
    label: str
    phrase: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    c: object | None = None
    world: object | None = None
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c
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


SETTINGS = {
    "fortress": Setting(place="the little fortress headquarters", affords={"rest", "read"}),
    "home": Setting(place="the cozy house", affords={"rest", "read", "snack"}),
    "clinic": Setting(place="the bright clinic waiting room", affords={"rest", "read"}),
}

ACTIONS = {
    "patrol": Activity(
        id="patrol",
        verb="patrol the neighborhood",
        gerund="patrolling the neighborhood",
        rush="dash outside to patrol",
        risk="overdo the hero work and feel worse",
        keyword="patrol",
        tags={"hero", "outside"},
    ),
    "fly": Activity(
        id="fly",
        verb="fly over the rooftops",
        gerund="flying over the rooftops",
        rush="zoom up into the sky",
        risk="strain the sick body and make the mumps hurt more",
        keyword="fly",
        tags={"hero", "sky"},
    ),
    "rescue": Activity(
        id="rescue",
        verb="rush out to rescue the lost kite",
        gerund="rushing out to rescue the lost kite",
        rush="run off to rescue the kite",
        risk="tire out the hero and spread the mumps germs",
        keyword="rescue",
        tags={"hero", "helper"},
    ),
}

COMFORTS = {
    "crouton": Comfort(
        id="crouton",
        label="crouton snack",
        phrase="a tiny bowl of crunchy croutons",
        prep="make a small bowl of croutons and soup",
        tail="sat under the blanket fort and munched the crunchy croutons",
        helps={"rest", "cheer"},
    ),
    "blanket": Comfort(
        id="blanket",
        label="blanket fort",
        phrase="a soft blanket fort",
        prep="build a blanket fort in the living room",
        tail="nestled into the blanket fort and read comic books",
        helps={"rest", "read"},
    ),
    "comic": Comfort(
        id="comic",
        label="comic book",
        phrase="a shiny comic book",
        prep="bring out the comic books",
        tail="turned the pages and imagined a calmer kind of hero day",
        helps={"read", "cheer"},
    ),
}

HERO_NAMES = ["Max", "Ivy", "Noah", "Zoe", "Pip", "Luna", "Tess", "Milo"]
PARENT_NAMES = ["Mom", "Dad"]
TRAITS = ["brave", "curious", "spunky", "gentle", "bold"]


def at_risk(activity: Activity, comfort: Comfort) -> bool:
    return activity.id in {"fly", "patrol", "rescue"} and "rest" in comfort.helps


def select_comfort(activity: Activity, comfort: Comfort) -> Optional[Comfort]:
    if activity.id in {"fly", "patrol", "rescue"} and comfort.id in {"crouton", "blanket", "comic"}:
        return comfort
    return None


def predict_bad(world: World, hero: Entity, activity: Activity) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(hero.id), activity, narrate=False)
    return {
        "hurt": sim.get(hero.id).memes.get("worry", 0.0) >= THRESHOLD,
        "fatigue": sim.get(hero.id).meters.get("fatigue", 0.0),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.meters["fatigue"] = actor.meters.get("fatigue", 0.0) + 1.0
    actor.memes["longing"] = actor.memes.get("longing", 0.0) + 1.0
    actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1.0
    if narrate:
        world.say(f"{actor.id} wanted to {activity.verb}, even while feeling the tug of being sick.")


def rule_rest(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.meters.get("fatigue", 0.0) < THRESHOLD:
            continue
        sig = ("rest", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["sigh"] = hero.memes.get("sigh", 0.0) + 1.0
        out.append(f"{hero.id} needed to slow down and rest.")
    return out


def rule_comfort(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.memes.get("sigh", 0.0) < THRESHOLD:
            continue
        if world.facts.get("comfort") is None:
            continue
        comfort = _safe_fact(world, world.facts, "comfort")
        sig = ("comfort", hero.id, comfort.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["cheer"] = hero.memes.get("cheer", 0.0) + 1.0
        out.append(f"{hero.id} felt a little better with a gentle plan.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (rule_rest, rule_comfort):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "brave")
    world.say(f"{hero.id} was a little {trait} superhero who loved helping people.")


def inner_monologue(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"Inside, {hero.id} thought, \"I can still be a hero. I just have to be a careful hero today.\""
    )
    world.say(
        f"Then {hero.pronoun('subject')} looked at the window and thought about {activity.gerund}, "
        f"because hero days were hard to give up."
    )


def diagnose(world: World, parent: Entity, hero: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    world.say(
        f"{parent.id} checked {hero.pronoun('possessive')} swollen cheeks and said {hero.id} had mumps."
    )
    world.say(
        f"\"No marching, no zooming, and no rescue runs today,\" {parent.id} said softly."
    )


def wants_to_go(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} wanted to {activity.verb}, but the idea made {hero.pronoun('possessive')} head feel heavy."
    )


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity) -> Optional[Comfort]:
    comfort = world.facts.get("comfort")
    if comfort is None:
        return None
    if predict_bad(world, hero, activity)["hurt"]:
        world.say(
            f"{parent.id} noticed that a real hero choice was to stay home and get better first."
        )
    world.say(
        f"Instead, {parent.id} said, \"Let's make your {comfort.label} mission now.\""
    )
    return comfort


def accept(world: World, hero: Entity, comfort: Comfort) -> None:
    hero.memes["cheer"] = hero.memes.get("cheer", 0.0) + 1.0
    hero.memes["worry"] = 0.0
    world.say(
        f"{hero.id}'s eyes brightened. {hero.pronoun('subject').capitalize()} nodded and smiled."
    )
    world.say(
        f"They {comfort.prep}, and soon {hero.id} {comfort.tail}."
    )


def tell(setting: Setting, activity: Activity, comfort: Comfort, hero_name: str, parent_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type="boy" if hero_name not in {"Ivy", "Zoe", "Luna", "Tess"} else "girl",
        traits=["little", trait, "heroic"],
    ))
    parent = world.add(Entity(id=parent_name, kind="character", type="mother" if parent_name == "Mom" else "father"))
    sickness = world.add(Entity(
        id="mumps", type="thing", label="mumps", phrase="mumps",
        owner=hero.id, caretaker=parent.id,
    ))
    snack = world.add(Entity(
        id=comfort.id, type="thing", label=comfort.label, phrase=comfort.phrase,
        owner=hero.id, caretaker=parent.id,
    ))
    hero.memes["longing"] = 1.0
    hero.memes["worry"] = 1.0

    intro(world, hero)
    inner_monologue(world, hero, activity)
    diagnose(world, parent, hero)

    world.para()
    wants_to_go(world, hero, activity)
    world.say(f"{hero.id} thought, \"But my cape wants action!\"")
    world.say(f"Still, {hero.id} knew {activity.risk} would not help.")
    world.say(
        f"{parent.id} pointed to the couch at {world.setting.place} and asked for a quiet day."
    )
    propagate(world, narrate=True)

    world.para()
    world.facts.update(hero=hero, parent=parent, sickness=sickness, comfort=snack, activity=activity, setting=setting)
    chosen = compromise(world, parent, hero, activity)
    if chosen:
        accept(world, hero, chosen)
    world.say(
        f"By the end, {hero.id} was not flying anywhere, but {hero.pronoun('subject')} was still a superhero who rested wisely."
    )

    world.facts["resolved"] = True
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for comfort_id in COMFORTS:
                if act_id in {"fly", "patrol", "rescue"} and comfort_id in {"crouton", "blanket", "comic"}:
                    combos.append((place, act_id, comfort_id))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    comfort: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, comfort = f["hero"], f["parent"], f["activity"], f["comfort"]
    return [
        f'Write a gentle superhero story for a small child that includes the word "{comfort.id}" and the word "mumps".',
        f"Tell a story where {hero.id} wants to {act.verb} but {parent.id} knows the child needs rest, and the child uses an inner monologue.",
        f"Write a short superhero tale in which a hero with mumps chooses a safe plan and enjoys a {comfort.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, act, comfort = f["hero"], f["parent"], f["activity"], f["comfort"]
    return [
        QAItem(
            question=f"What kind of day did {hero.id} want before {parent.id} told them to rest?",
            answer=f"{hero.id} wanted a hero day of {act.gerund}, but the sickness made that a bad idea.",
        ),
        QAItem(
            question=f"Why did {parent.id} stop {hero.id} from {act.verb}?",
            answer=f"Because {hero.id} had mumps, and {act.risk} would only make the day harder.",
        ),
        QAItem(
            question=f"What helped {hero.id} feel better at the end?",
            answer=f"The {comfort.label} plan helped {hero.id} feel calmer, and the crunchy croutons made resting feel special.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = [
        QAItem(
            question="What are mumps?",
            answer="Mumps is an illness that can make a child's cheeks swell and make them feel tired.",
        ),
        QAItem(
            question="What is a crouton?",
            answer="A crouton is a small crunchy piece of toasted bread, often put on soup or salad.",
        ),
    ]
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="home", activity="fly", comfort="crouton", name="Max", parent="Mom", trait="brave"),
    StoryParams(place="fortress", activity="patrol", comfort="blanket", name="Zoe", parent="Dad", trait="spunky"),
    StoryParams(place="home", activity="rescue", comfort="comic", name="Pip", parent="Mom", trait="gentle"),
]


def explain_rejection(activity: Activity, comfort: Comfort) -> str:
    if activity.id not in {"patrol", "fly", "rescue"}:
        return "(No story: that activity is not a superhero-sized challenge in this tiny world.)"
    if comfort.id not in {"crouton", "blanket", "comic"}:
        return "(No story: the comfort choice does not fit this hero-resting story.)"
    return "(No story: nothing in this combination creates the needed rest-versus-hero-work tension.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("risk", aid, a.risk))
    for cid, c in COMFORTS.items():
        lines.append(asp.fact("comfort", cid))
        for h in sorted(c.helps):
            lines.append(asp.fact("helps", cid, h))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Act, Comfort) :- affords(Place, Act), activity(Act), comfort(Comfort),
                              risk(Act, _), helps(Comfort, rest).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, p = set(asp_valid_combos()), set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - p:
        print(" only in clingo:", sorted(a - p))
    if p - a:
        print(" only in python:", sorted(p - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with mumps, croutons, and inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIONS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["Mom", "Dad"])
    ap.add_argument("--trait", choices=TRAITS)
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
              and (getattr(args, "comfort", None) is None or c[2] == getattr(args, "comfort", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, comfort = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENT_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, comfort=comfort, name=name, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIONS, params.activity), _safe_lookup(COMFORTS, params.comfort), params.name, params.parent, params.trait)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, comfort) combos:\n")
        for c in combos:
            print("  ", c)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} (comfort: {p.comfort})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
