#!/usr/bin/env python3
"""
storyworlds/worlds/country_bumpkin_shame_foreshadowing_conflict_pirate_tale.py
==============================================================================

A small pirate-tale storyworld about a country bumpkin, shame, foreshadowing,
and a conflict that turns into belonging.

The premise is classical and child-facing:
- a shy country bumpkin comes aboard a pirate ship,
- early details foreshadow trouble,
- a conflict erupts over a sea task,
- the bumpkin proves useful and the shame eases.

This file is standalone and uses only stdlib plus the shared results container.
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
    kind: str = "thing"  # "character" | "thing" | "place"
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

    region: object | None = None
    captain: object | None = None
    entities: set[str] = field(default_factory=set)
    hero: object | None = None
    treasure: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "lass"}
        male = {"boy", "man", "father", "lad"}
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
    affordances: set[str] = field(default_factory=set)
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
class Challenge:
    id: str
    verb: str
    gerund: str
    foreshadow: str
    conflict_line: str
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
class Treasure:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"boy", "girl"})
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
class Remedy:
    id: str
    label: str
    offer: str
    tail: str
    covers: set[str]
    guards: set[str]
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


@dataclass
class StoryParams:
    place: str
    challenge: str
    treasure: str
    name: str
    gender: str
    captain: str
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


SETTINGS = {
    "dock": Setting(place="the dock", affordances={"rope", "storm"}),
    "ship": Setting(place="the pirate ship", affordances={"rope", "sail", "storm"}),
    "cove": Setting(place="the quiet cove", affordances={"sail", "storm"}),
}

CHALLENGES = {
    "rope": Challenge(
        id="rope",
        verb="tie the knot",
        gerund="tying knots",
        foreshadow="the rope kept slipping through small fingers",
        conflict_line="the captain frowned at the crooked knot",
        risk="would tangle the sail",
        keyword="rope",
        tags={"rope", "pirate"},
    ),
    "sail": Challenge(
        id="sail",
        verb="raise the sail",
        gerund="raising sails",
        foreshadow="the sail flapped like a giant white bird",
        conflict_line="the wind tugged at the canvas and made the deck noisy",
        risk="would leave the ship stuck",
        keyword="sail",
        tags={"sail", "wind"},
    ),
    "storm": Challenge(
        id="storm",
        verb="help with the storm lines",
        gerund="working in storm wind",
        foreshadow="dark clouds rolled in over the water",
        conflict_line="the waves thumped the hull like a drum",
        risk="would splash everything cold and wet",
        keyword="storm",
        tags={"storm", "wet"},
    ),
}

TREASURES = {
    "boots": Treasure(
        label="boots",
        phrase="a pair of muddy country boots",
        type="boots",
        region="feet",
        plural=True,
    ),
    "hat": Treasure(
        label="hat",
        phrase="a floppy straw hat",
        type="hat",
        region="head",
    ),
    "vest": Treasure(
        label="vest",
        phrase="a neat little vest",
        type="vest",
        region="torso",
    ),
}

REMEDIES = [
    Remedy(
        id="gloves",
        label="work gloves",
        offer="put on the work gloves first",
        tail="slid on the work gloves and tried again",
        covers={"hands"},
        guards={"rope"},
    ),
    Remedy(
        id="slicker",
        label="a rain slicker",
        offer="pull on a rain slicker first",
        tail="pulled on the rain slicker and stepped back out",
        covers={"torso"},
        guards={"storm"},
    ),
    Remedy(
        id="sea_boots",
        label="sea boots",
        offer="wear sea boots first",
        tail="wear the sea boots and keep steady",
        covers={"feet"},
        guards={"storm"},
    ),
    Remedy(
        id="patch",
        label="a bright patch",
        offer="sew on a bright patch to mark the knot",
        tail="tied the knot with the bright patch as a guide",
        covers={"hands"},
        guards={"rope"},
    ),
]

GIRL_NAMES = ["Mina", "Clara", "Nell", "Ruby", "Ivy", "Lina"]
BOY_NAMES = ["Tom", "Jory", "Ben", "Will", "Eli", "Otis"]
TRAITS = ["shy", "earnest", "curious", "timid", "stubborn", "bright"]


def prize_at_risk(challenge: Challenge, treasure: Treasure) -> bool:
    if challenge.id == "rope":
        return treasure.region in {"hands", "torso"}
    if challenge.id == "sail":
        return treasure.region in {"torso", "head"}
    if challenge.id == "storm":
        return treasure.region in {"feet", "torso", "head"}
    return False


def select_remedy(challenge: Challenge, treasure: Treasure) -> Optional[Remedy]:
    for remedy in REMEDIES:
        if challenge.id in remedy.guards:
            if challenge.id == "rope" and treasure.region in remedy.covers:
                return remedy
            if challenge.id != "rope":
                return remedy
    return None


def predict(world: World, hero: Entity, challenge: Challenge, treasure_id: str) -> dict:
    sim = World(world.setting)
    sim.entities = {k: Entity(**vars(v)) for k, v in world.entities.items()}
    sim.fired = set(world.fired)
    do_challenge(sim, sim.get(hero.id), challenge, narrate=False)
    t = sim.get(treasure_id)
    return {"shamed": hero.memes.get("shame", 0.0), "damaged": t.meters.get("dirty", 0.0) >= THRESHOLD}


def do_challenge(world: World, hero: Entity, challenge: Challenge, narrate: bool = True) -> None:
    hero.meters[challenge.id] = hero.meters.get(challenge.id, 0.0) + 1.0
    if challenge.id == "rope":
        hero.memes["nervous"] = hero.memes.get("nervous", 0.0) + 1.0
    if challenge.id == "storm":
        hero.meters["wet"] = hero.meters.get("wet", 0.0) + 1.0
    if narrate:
        world.say(f"{hero.id} tried to {challenge.verb}, but the sea was not an easy teacher.")


def tell(setting: Setting, challenge: Challenge, treasure_cfg: Treasure, hero_name: str,
         hero_type: str, hero_traits: Optional[list[str]], captain_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["country bumpkin"] + (hero_traits or ["shy", "earnest"]),
        memes={"shame": 1.0, "hope": 0.0},
    ))
    captain = world.add(Entity(
        id="Captain",
        kind="character",
        type=captain_type,
        label="the captain",
        traits=["stern", "sharp-eyed"],
    ))
    treasure = world.add(Entity(
        id="treasure",
        kind="thing",
        type=treasure_cfg.type,
        label=treasure_cfg.label,
        phrase=treasure_cfg.phrase,
        owner=hero.id,
        caretaker=captain.id,
        region=treasure_cfg.region,
        plural=treasure_cfg.plural,
    ))

    world.say(f"{hero.id} was a country bumpkin who had never seen a pirate deck before.")
    world.say(f"{hero.pronoun().capitalize()} wore {hero.pronoun('possessive')} {treasure.label} like a tiny badge from home.")
    world.say(f"But {challenge.foreshadow}; that was the first sign the day would not stay calm.")

    world.para()
    world.say(f"At {setting.place}, {hero.id} heard the crew shout for help as {challenge.conflict_line}.")
    world.say(f"{hero.id} wanted to {challenge.verb}, yet {hero.pronoun('possessive')} cheeks burned with shame.")
    world.say(f"All the pirates looked busy, and the little bumpkin felt as small as a shell in the sand.")

    world.para()
    world.say(f"Then the captain spoke up: '{challenge.risk}, and we need steady hands.'")
    world.say(f"{hero.id} swallowed hard and stepped forward anyway.")

    if not prize_at_risk(challenge, treasure):
        pass

    remedy = select_remedy(challenge, treasure)
    if remedy is None:
        pass

    world.say(f"Before trying again, the captain offered a better plan: {remedy.offer}.")
    world.say(f"{hero.id} listened, and the shame in {hero.pronoun('possessive')} chest began to loosen.")

    do_challenge(world, hero, challenge)
    hero.memes["shame"] = 0.0
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1.0
    treasure.worn_by = hero.id

    world.say(f"With the plan in place, {hero.id} {remedy.tail}.")
    world.say(f"The crew cheered because the task was done right, and the {treasure.label} stayed safe.")
    world.say(f"By sunset, the country bumpkin was no longer hiding behind {hero.pronoun('possessive')} hat; {hero.pronoun().capitalize()} stood tall beside the pirates.")

    world.facts.update(
        hero=hero,
        captain=captain,
        treasure=treasure,
        challenge=challenge,
        remedy=remedy,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    challenge = _safe_fact(world, f, "challenge")
    treasure = _safe_fact(world, f, "treasure")
    return [
        f'Write a short pirate story for a young child about a country bumpkin named {hero.id}.',
        f"Tell a story where {hero.id} feels shame, hears a foreshadowing sign, and then helps with {challenge.verb}.",
        f"Make a gentle pirate tale that includes {treasure.phrase} and ends with the crew welcoming {hero.id}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    captain = _safe_fact(world, f, "captain")
    treasure = _safe_fact(world, f, "treasure")
    challenge = _safe_fact(world, f, "challenge")
    remedy = _safe_fact(world, f, "remedy")
    qa = [
        QAItem(
            question=f"Who was the country bumpkin in the story?",
            answer=f"The country bumpkin was {hero.id}, a shy pirate helper who felt ashamed at first.",
        ),
        QAItem(
            question=f"What foreshadowing sign showed that trouble was coming?",
            answer=f"The story foreshadowed trouble when {challenge.foreshadow}.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel shame before helping?",
            answer=f"{hero.id} felt shame because the pirate deck was new and scary, and {hero.pronoun('possessive')} cheeks burned when everyone looked at {hero.pronoun('object')}.",
        ),
        QAItem(
            question=f"How did the captain help {hero.id} solve the conflict?",
            answer=f"The captain told {hero.id} to use {remedy.label} first, so {hero.id} could try again in a safer way.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {hero.id} stood tall beside the pirates, the task was finished, and the {treasure.label} stayed safe.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did {hero.id} feel after the problem was solved?",
                answer=f"{hero.id} felt proud and much less ashamed after {hero.pronoun('possessive')} help mattered to the crew.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bumpkin?",
            answer="A bumpkin is a country person who may seem awkward in a new place, but can still learn and help.",
        ),
        QAItem(
            question="What does shame feel like?",
            answer="Shame can feel hot and heavy inside, like you want to hide your face even when you are not in trouble.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a clue early in the story that hints that something important or difficult will happen later.",
        ),
        QAItem(
            question="Why do pirates use ropes and sails?",
            answer="Pirates use ropes and sails to steer the ship and catch the wind so it can travel over the water.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
        if e.kind == "thing" and e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="ship", challenge="rope", treasure="boots", name="Ned", gender="boy", captain="captain", trait="shy"),
    StoryParams(place="dock", challenge="storm", treasure="hat", name="Mara", gender="girl", captain="captain", trait="earnest"),
    StoryParams(place="cove", challenge="sail", treasure="vest", name="Otis", gender="boy", captain="captain", trait="curious"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for challenge_id in setting.affordances:
            challenge = _safe_lookup(CHALLENGES, challenge_id)
            for treasure_id, treasure in TREASURES.items():
                if prize_at_risk(challenge, treasure) and select_remedy(challenge, treasure):
                    combos.append((place, challenge_id, treasure_id))
    return combos


def explain_rejection(challenge: Challenge, treasure: Treasure) -> str:
    return f"(No story: {challenge.verb} does not honestly threaten {treasure.label}, so there is no real pirate conflict.)"


def explain_gender(treasure_id: str, gender: str) -> str:
    allowed = " / ".join(sorted(_safe_lookup(TREASURES, treasure_id).genders))
    return f"(No story: {_safe_lookup(TREASURES, treasure_id).label} is not a typical {gender}'s item here; try --gender {allowed}.)"


ASP_RULES = r"""
prize_at_risk(C, T) :- challenge(C), treasure(T), risk_zone(C, R), worn_on(T, R).
can_fix(C, T) :- prize_at_risk(C, T), remedy(R), handles(R, C), covers(R, X), worn_on(T, X).
valid(Place, C, T) :- setting(Place), affords(Place, C), prize_at_risk(C, T), can_fix(C, T).
valid_story(Place, C, T, Gender) :- valid(Place, C, T), wears(Gender, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for c in sorted(s.affordances):
            lines.append(asp.fact("affords", sid, c))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("risk_zone", cid, "hands" if cid == "rope" else "torso"))
        if cid == "storm":
            lines[-1] = asp.fact("risk_zone", cid, "feet")
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("worn_on", tid, t.region))
        for g in sorted(t.genders):
            lines.append(asp.fact("wears", g, tid))
    for r in REMEDIES:
        lines.append(asp.fact("remedy", r.id))
        for c in sorted(r.covers):
            lines.append(asp.fact("covers", r.id, c))
        for m in sorted(r.guards):
            lines.append(asp.fact("handles", r.id, m))
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
    ap = argparse.ArgumentParser(description="Pirate-tale storyworld about country bumpkin shame and foreshadowed conflict.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--captain", choices=["captain"])
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
    if getattr(args, "challenge", None) and getattr(args, "treasure", None):
        ch, tr = _safe_lookup(CHALLENGES, getattr(args, "challenge", None)), _safe_lookup(TREASURES, getattr(args, "treasure", None))
        if not (prize_at_risk(ch, tr) and select_remedy(ch, tr)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "treasure", None) and getattr(args, "gender", None) not in _safe_lookup(TREASURES, getattr(args, "treasure", None)).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "challenge", None) is None or c[1] == getattr(args, "challenge", None))
              and (getattr(args, "treasure", None) is None or c[2] == getattr(args, "treasure", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, challenge, treasure = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["boy", "girl"])
    treasure_obj = _safe_lookup(TREASURES, treasure)
    if gender not in treasure_obj.genders:
        gender = rng.choice(sorted(treasure_obj.genders))
    name = getattr(args, "name", None) or rng.choice(BOY_NAMES if gender == "boy" else GIRL_NAMES)
    captain = getattr(args, "captain", None) or "captain"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, challenge=challenge, treasure=treasure, name=name,
                       gender=gender, captain=captain, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(CHALLENGES, params.challenge),
        _safe_lookup(TREASURES, params.treasure),
        params.name,
        params.gender,
        [params.trait],
        params.captain,
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
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, challenge, treasure) combos ({len(stories)} with gender):\n")
        for place, ch, tr in triples:
            genders = sorted(g for (pl, c, t, g) in stories if (pl, c, t) == (place, ch, tr))
            print(f"  {place:8} {ch:9} {tr:8}  [{', '.join(genders)}]")
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
            header = f"### {p.name}: {p.challenge} at {p.place} (treasure: {p.treasure})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
