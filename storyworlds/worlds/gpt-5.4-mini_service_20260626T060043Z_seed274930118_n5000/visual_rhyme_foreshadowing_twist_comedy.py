#!/usr/bin/env python3
"""
A tiny storyworld about a visual show, a rhyme, a foreshadowed mix-up, and a
comic twist.

Premise:
- A child prepares a visual rhyme show with painted cards, bright props, and a
  big idea.
- A clue appears early: one prop looks useful in the wrong way.
- The child tries the plan, hits the mismatch, and learns the real use.
- The ending proves the twist with a cheerful final image.

This script is self-contained and follows the Storyweavers storyworld contract.
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    helper: object | None = None
    hero: object | None = None
    parent: object | None = None
    prop: object | None = None
    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
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
    indoors: bool = True
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
    risk: str
    clue: str
    mishap: str
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
class Prop:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    kinds: set[str] = field(default_factory=set)
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
class Aid:
    id: str
    label: str
    prep: str
    tail: str
    protects: set[str]
    fits: set[str]
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def carried(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]


def has_match(activity: Activity, prop: Prop) -> bool:
    return prop.region in activity.zone and (not prop.kinds or activity.id in prop.kinds or bool(activity.tags & prop.kinds))


def select_aid(activity: Activity, prop: Prop) -> Optional[Aid]:
    for aid in AID_CATALOG:
        if prop.region in aid.protects and activity.id in aid.fits:
            return aid
    return None


def predict_mishap(world: World, actor: Entity, activity: Activity, prop: Entity) -> bool:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    return sim.get(prop.id).meter("smudged") >= THRESHOLD or sim.get(prop.id).meter("tipped") >= THRESHOLD


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        pass
    actor.meters[activity.id] = actor.meter(activity.id) + 1
    for ent in list(world.entities.values()):
        if ent.owner == actor.id and ent.region in activity.zone:
            ent.meters["smudged"] = ent.meter("smudged") + 1
            if narrate:
                world.say(f"{ent.label.capitalize()} got a little smudged in the bright bustle.")
    if narrate:
        world.say(f"{actor.id} did {activity.gerund}, and the whole room felt lively.")


def visual_detail(setting: Setting) -> str:
    return {
        "studio": "The studio lights blinked like friendly fireflies.",
        "classroom": "The classroom wall held up a big blank board, waiting for color.",
        "kitchen": "The kitchen table shone, ready for paper, paint, and a proper mess.",
    }.get(setting.place, f"{setting.place.capitalize()} looked neat and bright.")


def rhyme_line(activity: Activity) -> str:
    return {
        "paint": "Paint on a card can dazzle and zap, then laugh when it slips into a lap.",
        "sticker": "A sticker may shimmer, a sticker may stick, but a peeled-up corner can turn rather quick.",
        "glisten": "If glitter goes flying, it sparkles and skips, then settles like sugar on sleeves and lips.",
    }.get(activity.id, "A bright little rhyme can hop and play, and bounce a surprise into the day.")


def foreshadow(world: World, actor: Entity, prop: Prop, activity: Activity) -> None:
    world.say(
        f"Before the show, {actor.id} noticed {prop.phrase}. "
        f"It looked important, which was a clue, because a clue can be funny later."
    )
    world.say(f'"{rhyme_line(activity)}" {actor.id} whispered, grinning at the shiny setup.')


def twist(world: World, actor: Entity, prop: Prop, activity: Activity) -> None:
    if prop.meter("smudged") < THRESHOLD and prop.meter("tipped") < THRESHOLD:
        world.say(f"Nothing went wrong after all, which was not funny enough for this world.")
        return
    world.say(
        f"Then came the twist: {prop.label} was not a stage prop at all. "
        f"It was the thing that solved the whole show."
    )


def resolve(world: World, actor: Entity, parent: Entity, prop: Prop, activity: Activity, aid: Optional[Aid]) -> None:
    actor.memes["joy"] = actor.meme("joy") + 1
    actor.memes["pride"] = actor.meme("pride") + 1
    if aid is not None:
        world.say(
            f'{parent.id} smiled and said, "Let\'s use the {aid.label} first." '
            f"{aid.tail.capitalize()}."
        )
    world.say(
        f"In the end, {actor.id} held up {prop.phrase}, now neat and ready, "
        f"and the room turned into a bright little laugh with colors in it."
    )


def tell(setting: Setting, activity: Activity, prop_cfg: Prop, hero_name: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl", traits=["curious", "cheerful"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="grown-up helper"))
    prop = world.add(Entity(
        id="prop",
        type=prop_cfg.id,
        label=prop_cfg.label,
        phrase=prop_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prop_cfg.region,
        plural=prop_cfg.plural,
    ))

    world.say(f"{hero.id} was a little visual thinker who loved bright lines and funny pictures.")
    world.say(f"{hero.id} wanted to {activity.verb} for the show, and everything looked ready.")
    world.say(visual_detail(setting))
    world.say(f"On the table sat {prop.phrase}.")
    world.para()

    foreshadow(world, hero, prop, activity)
    world.para()

    do_activity(world, hero, activity)
    if predict_mishap(world, hero, activity, prop):
        prop.meters["smudged"] = prop.meter("smudged") + 1
        world.say(
            f"{hero.id} tried the first version anyway, and {prop.label} got smudged fast. "
            f"That was the part everyone should have seen coming."
        )
    aid = select_aid(activity, prop_cfg)
    if aid:
        helper = world.add(Entity(
            id=aid.id,
            type="tool",
            label=aid.label,
            owner=hero.id,
            caretaker=parent.id,
            plural=aid.plural,
        ))
        helper.carried_by = hero.id
        world.say(
            f"{parent.id} spotted the fix and handed over {aid.label}. "
            f"{aid.prep.capitalize()}, and the room gasped with happy surprise."
        )
    else:
        helper = None
    twist(world, hero, prop, activity)
    resolve(world, hero, parent, prop_cfg, activity, aid)
    world.facts.update(hero=hero, parent=parent, prop=prop, activity=activity, setting=setting, aid=aid)
    return world


SETTINGS = {
    "studio": Setting(place="studio", indoors=True, affords={"paint", "sticker", "glisten"}),
    "classroom": Setting(place="classroom", indoors=True, affords={"paint", "sticker"}),
    "kitchen": Setting(place="kitchen", indoors=True, affords={"paint", "glisten"}),
}

ACTIVITIES = {
    "paint": Activity(
        id="paint",
        verb="paint a picture",
        gerund="painting a picture",
        risk="paint on the hands and sleeves",
        clue="a paint tray with a tiny blue drip",
        mishap="smudged",
        zone={"torso", "hands"},
        tags={"visual", "color", "messy"},
    ),
    "sticker": Activity(
        id="sticker",
        verb="make a sticker scene",
        gerund="arranging sticker scenes",
        risk="stickers on the board",
        clue="a sticker sheet with one corner peeled up",
        mishap="tipped",
        zone={"hands", "torso"},
        tags={"visual", "sticky", "laugh"},
    ),
    "glisten": Activity(
        id="glisten",
        verb="build a glistening picture",
        gerund="making glistening pictures",
        risk="sparkly dust on sleeves",
        clue="a glitter jar that winked in the light",
        mishap="smudged",
        zone={"torso", "hands"},
        tags={"visual", "sparkle", "laugh"},
    ),
}

PRIZES = {
    "poster": Prop(id="poster", label="poster board", phrase="a big poster board", region="torso", kinds={"paint", "sticker", "glisten"}),
    "apron": Prop(id="apron", label="apron", phrase="a neat little apron", region="torso", kinds={"paint", "glisten"}),
    "hat": Prop(id="hat", label="hat", phrase="a bright paper hat", region="torso", kinds={"sticker", "glisten"}),
}

AID_CATALOG = [
    Aid(id="apron", label="apron", prep="put on the apron", tail="The apron did its job", protects={"torso"}, fits={"paint", "glisten"}),
    Aid(id="clipboard", label="clipboard", prep="use the clipboard as a dry backer", tail="The clipboard kept the page steady", protects={"torso"}, fits={"sticker"}),
    Aid(id="tray", label="paint tray", prep="set the tray under the page", tail="The tray caught the drips", protects={"torso"}, fits={"paint", "glisten"}),
]

HERO_NAMES = ["Mia", "Nora", "Luca", "Ivy", "Zane", "Ruby"]
TRAITS = ["curious", "cheerful", "playful", "inventive"]


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    act = _safe_fact(world, f, "activity")
    return [
        f'Write a short funny story for a child about visual art, a rhyme, and a twist, using the word "visual".',
        f"Tell a comedy story where {hero.id} wants to {act.verb} in a bright room and a clue appears before the surprise.",
        f"Write a tiny story with a visual joke, a foreshadowed mishap, and a happy ending with colors and laughter.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    prop = _safe_fact(world, f, "prop")
    act = _safe_fact(world, f, "activity")
    aid = f.get("aid")
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do in the story?",
            answer=f"{hero.id} wanted to {act.verb}. It was part of a bright visual show.",
        ),
        QAItem(
            question=f"What clue was seen before the surprise?",
            answer=f"The clue was {act.clue}. That small detail hinted that the setup would matter later.",
        ),
        QAItem(
            question=f"Why did {prop.label} matter so much?",
            answer=f"{prop.phrase} mattered because it was the thing everyone was trying to keep neat for the show.",
        ),
    ]
    if aid is not None:
        qa.append(
            QAItem(
                question=f"How did the {aid.label} help?",
                answer=f"The {aid.label} helped by making the work steadier and cleaner, so the visual idea could finish without a bigger mess.",
            )
        )
    qa.append(
        QAItem(
            question=f"What was funny about the ending?",
            answer=f"The funny part was that the thing that looked like a possible problem turned out to be useful, so the twist became a happy joke.",
        )
    )
    return qa


KNOWLEDGE = {
    "visual": [
        QAItem(
            question="What does visual mean?",
            answer="Visual means something you can see with your eyes, like a picture, a color, or a bright shape.",
        )
    ],
    "rhyme": [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like cat and hat.",
        )
    ],
    "foreshadowing": [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a small clue early so readers can guess that something important may happen later.",
        )
    ],
    "twist": [
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise change that makes you look at the story in a new way.",
        )
    ],
    "apron": [
        QAItem(
            question="What is an apron for?",
            answer="An apron is a piece of clothing that helps keep your clothes clean while you cook, paint, or do other messy work.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    tags.add("visual")
    if f.get("aid"):
        tags.add(f["aid"].id)
    out: list[QAItem] = []
    for tag, items in KNOWLEDGE.items():
        if tag in tags:
            out.extend(items)
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
        parts = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.region:
            parts.append(f"region={e.region}")
        if e.carried_by:
            parts.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="studio", activity="paint", prize="poster", name="Mia", parent="mother", trait="curious"),
    StoryParams(place="classroom", activity="sticker", prize="hat", name="Nora", parent="father", trait="cheerful"),
    StoryParams(place="kitchen", activity="glisten", prize="apron", name="Ruby", parent="mother", trait="playful"),
]


ASP_RULES = r"""
at_risk(A,P) :- activity(A), prop(P), zone(A,R), region(P,R).
has_aid(A,P) :- at_risk(A,P), aid(X), fits(X,A), protects(X,R), zone(A,R), region(P,R).
valid_story(Place,A,P) :- setting(Place), affords(Place,A), at_risk(A,P), has_aid(A,P).
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
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prop", pid))
        lines.append(asp.fact("region", pid, p.region))
    for x in AID_CATALOG:
        lines.append(asp.fact("aid", x.id))
        for r in sorted(x.protects):
            lines.append(asp.fact("protects", x.id, r))
        for f in sorted(x.fits):
            lines.append(asp.fact("fits", x.id, f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, s in SETTINGS.items():
        for act_id in s.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prop_id, prop in PRIZES.items():
                if has_match(act, prop) and select_aid(act, prop) is not None:
                    combos.append((place, act_id, prop_id))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
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
    ap = argparse.ArgumentParser(description="Story world: visual rhyme, foreshadowing, twist, comedy.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), params.name, params.parent)
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
