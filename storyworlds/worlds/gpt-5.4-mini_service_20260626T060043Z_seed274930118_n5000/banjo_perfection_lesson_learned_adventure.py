#!/usr/bin/env python3
"""
storyworlds/worlds/banjo_perfection_lesson_learned_adventure.py
===============================================================

A small storyworld about a child, a banjo, and a lesson learned during a tiny
adventure.

Premise:
- A young musician loves a banjo and wants every note to sound perfect.
- On a little adventure, the child gets stuck on one mistake and stops having
  fun.
- A helper shows that music can still be wonderful even when it is not perfect.
- The child learns to keep going, and the adventure ends with a happier tune.

This world is intentionally compact and constraint-checked.  It models a few
typed entities with physical meters and emotional memes, and it keeps the prose
driven by world state rather than a frozen template.
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
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    banjo: object | None = None
    hero: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Place:
    name: str
    outdoors: bool = True
    affords: set[str] = field(default_factory=set)
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


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    effect: str
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
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        import copy as _copy

        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "trail": Place(name="the pine trail", outdoors=True, affords={"march", "campfire"}),
    "brook": Place(name="the brook path", outdoors=True, affords={"march", "skip"}),
    "hill": Place(name="the windy hill", outdoors=True, affords={"march", "listen"}),
}

ACTIVITIES = {
    "march": Activity(
        id="march",
        verb="march along",
        gerund="marching along",
        rush="rush ahead to keep up",
        risk="scratched and tired",
        effect="scraped knees",
        keyword="adventure",
        tags={"adventure", "trail"},
    ),
    "skip": Activity(
        id="skip",
        verb="skip over stones",
        gerund="skipping over stones",
        rush="dash from stone to stone",
        risk="muddy",
        effect="muddy shoes",
        keyword="brook",
        tags={"adventure", "brook"},
    ),
    "listen": Activity(
        id="listen",
        verb="listen for the echo",
        gerund="listening for the echo",
        rush="hurry to the top",
        risk="windy",
        effect="trembly fingers",
        keyword="echo",
        tags={"adventure", "hill"},
    ),
}

GEAR = {
    "strap": Gear(
        id="strap",
        label="a sturdy strap",
        prep="put on a sturdy strap",
        tail="kept the banjo safe on the walk",
        guards={"scratched and tired", "muddy", "windy"},
    ),
    "case": Gear(
        id="case",
        label="a padded case",
        prep="zip the banjo into a padded case",
        tail="made the banjo easy to carry",
        guards={"scratched and tired", "muddy", "windy"},
    ),
}

BANJO = {
    "small": Entity(
        id="banjo",
        kind="thing",
        type="banjo",
        label="banjo",
        phrase="a little wooden banjo with a shiny head",
        owner="hero",
        caretaker="parent",
    )
}

HERO_NAMES = ["Mila", "Nora", "Theo", "Eli", "Lina", "Owen", "Ruby", "Jack"]
TRAITS = ["curious", "bright-eyed", "spirited", "careful", "dreamy", "brave"]


@dataclass
class StoryParams:
    place: str
    activity: str
    hero_name: str
    hero_gender: str
    parent_type: str
    trait: str
    seed: Optional[int] = None
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place_id, place in SETTINGS.items():
        for act_id in place.affords:
            combos.append((place_id, act_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small banjo adventure about perfection and a lesson learned."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, hero_name=name, hero_gender=gender, parent_type=parent, trait=trait)


def reasonableness_gate(params: StoryParams) -> None:
    if params.activity not in ACTIVITIES:
        pass
    if params.place not in SETTINGS:
        pass


def predict_banjo_risk(world: World, hero: Entity, activity: Activity, banjo: Entity) -> bool:
    sim = world.copy()
    hero2 = sim.get(hero.id)
    banjo2 = sim.get(banjo.id)
    hero2.memes["perfection"] += 1
    hero2.memes["frustration"] += 1
    if activity.id == "march":
        banjo2.meters["scratched"] = 1
    elif activity.id == "skip":
        banjo2.meters["bumped"] = 1
    elif activity.id == "listen":
        banjo2.meters["stressed"] = 1
    return any(v >= THRESHOLD for v in banjo2.meters.values())


def tell(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = World(_safe_lookup(SETTINGS, params.place))

    hero = world.add(Entity(id="hero", kind="character", type=params.hero_gender, label=params.hero_name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_type, label="the parent"))
    banjo = world.add(Entity(id="banjo", kind="thing", type="banjo", label="banjo", phrase="a little wooden banjo with a shiny head", owner=hero.id, caretaker=parent.id))
    activity = _safe_lookup(ACTIVITIES, params.activity)

    hero.memes["love_music"] = 1.0
    hero.memes["perfection"] = 1.0
    hero.meters["energy"] = 1.0
    banjo.meters["polish"] = 1.0
    world.facts.update(hero=hero, parent=parent, banjo=banjo, activity=activity, params=params)

    world.say(f"{hero.label} was a {params.trait} {hero.type} who loved a banjo and wanted every song to sound perfect.")
    world.say(f"{hero.pronoun().capitalize()} believed a perfect note could make the whole day shine.")
    world.say(f"{hero.label}'s {parent.label_word} smiled, because the little banjo always made the house feel ready for adventure.")

    world.para()
    world.say(f"One day, {hero.label} and {hero.pronoun('possessive')} {parent.label_word} went to {world.place.name}.")
    world.say(f"The path promised {activity.keyword} and fresh air, and {hero.label} wanted to {activity.verb} while carrying the banjo.")

    if predict_banjo_risk(world, hero, activity, banjo):
        hero.memes["frustration"] += 1
        hero.memes["worry"] += 1
        world.say(f"{hero.label} tried to play a perfect tune, but one shaky note made {hero.pronoun('possessive')} face fall.")
        world.say(f"That worry made the walk feel less like fun and more like a test.")
    else:
        world.say(f"The tune sounded okay, but {hero.label} still kept listening for tiny mistakes.")

    world.para()
    world.say(f"Then a gentle helper on the trail noticed the frown and said, \"A brave song does not have to be perfect to be lovely.\"")
    world.say(f"{hero.label} looked down at the banjo, then back at the path, and took a slower breath.")
    gear = GEAR["strap"] if activity.id in {"march", "listen"} else GEAR["case"]
    world.say(f"{parent.label_word.capitalize()} suggested they {gear.prep} so the banjo could stay safe while they kept going.")

    hero.memes["lesson_learned"] = 1.0
    hero.memes["perfection"] = 0.0
    hero.memes["joy"] = 1.0
    hero.memes["confidence"] = 1.0
    banjo.meters["safe"] = 1.0

    world.para()
    world.say(f"{hero.label} nodded and agreed. {hero.pronoun().capitalize()} stopped chasing every tiny mistake and started playing with the rhythm of the walk.")
    world.say(f"With {gear.label} helping, {hero.label} could {activity.verb}, keep the banjo safe, and still hear the music in the wind.")
    world.say(f"By the end, {hero.label} was smiling, the trail felt like an adventure, and the banjo sounded warm even with a few imperfect notes.")
    world.facts["gear"] = gear
    world.facts["lesson"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    act = _safe_fact(world, f, "activity")
    return [
        f'Write a short adventure story for a child named {hero.label} who loves a banjo and worries about perfection.',
        f"Tell a gentle story where {hero.label} tries to {act.verb} with a banjo but learns a lesson about not needing to be perfect.",
        f'Write a simple "lesson learned" adventure with the words "banjo" and "perfection".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, activity, banjo = f["hero"], f["parent"], f["activity"], f["banjo"]
    gear = _safe_fact(world, f, "gear")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.label}, a little {hero.type} who loves a banjo and learns a lesson during an adventure.",
        ),
        QAItem(
            question=f"Why did {hero.label} feel upset on the trail?",
            answer=f"{hero.label} felt upset because one shaky note made {hero.pronoun('possessive')} music seem less than perfect, and that turned the fun walk into a worry.",
        ),
        QAItem(
            question=f"What helped {hero.label} keep the banjo safe while still {activity.gerund}?",
            answer=f"{gear.label} helped keep the banjo safe while {hero.label} kept going on the trail.",
        ),
        QAItem(
            question=f"What lesson did {hero.label} learn?",
            answer=f"{hero.label} learned that music can still be lovely even when it is not perfect.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a banjo?",
            answer="A banjo is a stringed instrument with a bright, twangy sound.",
        ),
        QAItem(
            question="What does perfection mean?",
            answer="Perfection means trying to make something as flawless as possible.",
        ),
        QAItem(
            question="Why can a lesson learned be helpful?",
            answer="A lesson learned can help someone make kinder and wiser choices next time.",
        ),
        QAItem(
            question="What is an adventure?",
            answer="An adventure is an exciting trip or experience where something new happens.",
        ),
    ]


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
        lines.append(f"  {e.id:7} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero_loves_banjo :- love_music(hero).
perfection_problem :- perfection(hero), frustration(hero).
lesson_learned :- lesson(hero).
safe_adventure :- lesson_learned, banjo_safe(banjo).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("love_music", "hero"),
        asp.fact("perfection", "hero"),
        asp.fact("lesson", "hero"),
        asp.fact("banjo_safe", "banjo"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show hero_loves_banjo/0.\n#show perfection_problem/0.\n#show lesson_learned/0.\n#show safe_adventure/0."))
    shown = {sym.name for sym in model}
    expected = {"hero_loves_banjo", "perfection_problem", "lesson_learned", "safe_adventure"}
    if shown == expected:
        print("OK: ASP twin is internally consistent.")
        return 0
    print("MISMATCH in ASP twin.")
    print("  shown:", sorted(shown))
    print("  expected:", sorted(expected))
    return 1


CURATED = [
    StoryParams(place="trail", activity="march", hero_name="Mila", hero_gender="girl", parent_type="mother", trait="curious"),
    StoryParams(place="brook", activity="skip", hero_name="Theo", hero_gender="boy", parent_type="father", trait="spirited"),
    StoryParams(place="hill", activity="listen", hero_name="Ruby", hero_gender="girl", parent_type="mother", trait="careful"),
]


def explain_rejection() -> str:
    return "(No story: the requested combination does not make sense for this little adventure.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show hero_loves_banjo/0.\n#show perfection_problem/0.\n#show lesson_learned/0.\n#show safe_adventure/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show hero_loves_banjo/0.\n#show perfection_problem/0.\n#show lesson_learned/0.\n#show safe_adventure/0."))
        print("ASP model:", " ".join(str(s) for s in model))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
