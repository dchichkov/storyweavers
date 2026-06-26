#!/usr/bin/env python3
"""
A standalone storyworld for a tall-tale-style marsh story about cheating,
a bloom, and a friendship that ends badly.

The world is small and classical:
- a hero and a friend go to the marsh,
- one of them cheats in a little race or contest,
- a bloom is harmed,
- the friendship breaks in a bad ending.

The story is generated from simulated world state rather than a frozen paragraph.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    friend: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bloom: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mud": 0.0, "damage": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "cheat": 0.0, "hurt": 0.0, "anger": 0.0, "trust": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    id: str
    label: str
    watery: bool = False
    blooms: bool = False
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


@dataclass
class Challenge:
    id: str
    name: str
    verb: str
    shortcut: str
    consequence: str
    risk: str
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
class Bloom:
    id: str
    label: str
    phrase: str
    fragile: bool = True
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
    def __init__(self, place: Place, challenge: Challenge) -> None:
        self.place = place
        self.challenge = challenge
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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
        clone = World(self.place, self.challenge)
        import copy as _copy
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


PLACES = {
    "marsh": Place(id="marsh", label="the marsh", watery=True, blooms=True),
    "pond-edge": Place(id="pond-edge", label="the pond edge", watery=True, blooms=True),
    "reedbank": Place(id="reedbank", label="the reed bank", watery=True, blooms=True),
}

CHALLENGES = {
    "race": Challenge(
        id="race",
        name="marsh race",
        verb="race across the plank path",
        shortcut="cut through the reeds",
        consequence="won by cheating",
        risk="left the bloom bent and bruised",
    ),
    "stepdance": Challenge(
        id="stepdance",
        name="mud stepdance",
        verb="dance from stone to stone",
        shortcut="skip the hard part",
        consequence="won by cheating",
        risk="splashed the bloom flat",
    ),
    "berrycount": Challenge(
        id="berrycount",
        name="berry count",
        verb="count the bright berries",
        shortcut="snatch a better pile",
        consequence="won by cheating",
        risk="crushed the bloom in the rush",
    ),
}

BLOOMS = {
    "marsh-bloom": Bloom(
        id="marsh-bloom",
        label="bloom",
        phrase="a single lantern-colored bloom",
    ),
}

GIRL_NAMES = ["Mara", "Lena", "Ruby", "June", "Ivy", "Nell"]
BOY_NAMES = ["Otis", "Bo", "Finn", "Jasper", "Wade", "Theo"]
TRAITS = ["tall-talking", "brave", "merry", "plainspoken", "quick-footed", "stubborn"]


@dataclass
class StoryParams:
    place: str
    challenge: str
    name: str
    gender: str
    friend_name: str
    friend_gender: str
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
    ap = argparse.ArgumentParser(description="Tall-tale marsh storyworld with cheating, bloom damage, and bad-ending friendship fallout.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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


def reasonableness_gate(place: Place, challenge: Challenge) -> bool:
    return place.watery and place.blooms and challenge.id in CHALLENGES


def explain_rejection(place: Place, challenge: Challenge) -> str:
    return f"(No story: {challenge.name} does not fit {place.label}; the marsh tale needs water, a bloom, and a real chance for cheating.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place_id = getattr(args, "place", None) or rng.choice(list(PLACES))
    challenge_id = getattr(args, "challenge", None) or rng.choice(list(CHALLENGES))
    place = _safe_lookup(PLACES, place_id)
    challenge = _safe_lookup(CHALLENGES, challenge_id)
    if not reasonableness_gate(place, challenge):
        return _fallback_storyparams(args, rng, StoryParams, globals())

    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend_gender = getattr(args, "friend_gender", None) or ("boy" if gender == "girl" else "girl")
    friend_name = getattr(args, "friend_name", None) or rng.choice(BOY_NAMES if friend_gender == "boy" else GIRL_NAMES)
    trait = rng.choice(TRAITS)
    if friend_name == name:
        friend_name = friend_name + " Jr."
    return StoryParams(
        place=place_id,
        challenge=challenge_id,
        name=name,
        gender=gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        trait=trait,
    )


def _do_cheat(world: World, cheater: Entity, friend: Entity, bloom: Entity) -> None:
    cheater.memes["cheat"] += 1
    cheater.memes["trust"] -= 1
    friend.memes["hurt"] += 1
    friend.memes["anger"] += 1
    bloom.meters["damage"] += 1
    bloom.meters["mud"] += 1
    world.facts["cheated"] = True
    world.facts["friend_hurt"] = True
    world.facts["bloom_damaged"] = True


def tell(place: Place, challenge: Challenge, hero_name: str, hero_gender: str, friend_name: str, friend_gender: str, trait: str) -> World:
    world = World(place, challenge)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, traits=["tall-talking", trait]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, traits=["friend", "easy-going"]))
    bloom = world.add(Entity(id="bloom", kind="thing", type="flower", label="bloom"))
    hero.friend = friend.id
    friend.friend = hero.id

    world.say(f"There once was a {trait} {hero_gender} named {hero_name}, and {hero_name} had a friend named {friend_name}.")
    world.say(f"They were as close as two fence posts in a storm, and on every fair day they went down to {place.label} together.")
    world.say(f"At the edge of the reeds stood {bloom.phrase}, bright as a pocketful of sunrise, and both friends liked to look at it.")

    world.para()
    world.say(f"One big morning, the pair set out to {challenge.verb}.")
    world.say(f"{hero_name} wanted to win the old marsh way, with honest feet and a steady grin.")
    world.say(f"But {friend_name} found a sneaky {challenge.shortcut}, and {friend_name} used it to pull ahead.")
    _do_cheat(world, friend, hero, bloom)
    world.say(f"{friend_name} had cheated, and the win felt thin as pond scum on a breeze.")
    world.say(f"The rush also {challenge.risk}, and the little {bloom.label} bent low in the muck.")

    world.para()
    hero.memes["trust"] -= 1
    hero.memes["hurt"] += 1
    hero.memes["anger"] += 1
    world.facts["friendship_broken"] = True
    world.say(f"{hero_name} stared at {friend_name} with eyes as wide as moon puddles and said, 'That was not fair.'")
    world.say(f"{friend_name} tried to laugh it off, but the laughter came out small and hollow.")
    world.say(f"By sunset the two were no longer walking side by side.")
    world.say(f"The marsh kept its still water, the bloom stayed bruised, and the friendship ended in a bad way.")

    world.facts.update(
        hero=hero,
        friend=friend,
        bloom=bloom,
        place=place,
        challenge=challenge,
        trait=trait,
        hero_name=hero_name,
        friend_name=friend_name,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall tale for a young child about {f["hero_name"]} and {f["friend_name"]} at {f["place"].label}, where one friend cheats and a bloom gets hurt.',
        f'Tell a marsh story with the words "marsh", "cheat", and "bloom" that ends with friendship going wrong.',
        f'Write a simple tall tale about two friends, a sneaky shortcut, and a damaged bloom beside the water.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    friend: Entity = _safe_fact(world, f, "friend")  # type: ignore[assignment]
    bloom: Entity = _safe_fact(world, f, "bloom")  # type: ignore[assignment]
    challenge: Challenge = _safe_fact(world, f, "challenge")  # type: ignore[assignment]
    place: Place = _safe_fact(world, f, "place")  # type: ignore[assignment]

    return [
        QAItem(
            question=f"Who were the two friends in the story?",
            answer=f"The story was about {f['hero_name']} and {f['friend_name']}, two friends who went to {place.label} together.",
        ),
        QAItem(
            question=f"What did the cheating friend do?",
            answer=f"{f['friend_name']} used a sneaky {challenge.shortcut} instead of playing fairly.",
        ),
        QAItem(
            question=f"What got hurt near the water?",
            answer=f"The {bloom.label} got bent and bruised in the mud when the cheating happened.",
        ),
        QAItem(
            question=f"How did the friendship end?",
            answer="It ended badly, because the honest friend felt hurt and angry after the cheating.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a marsh?",
            answer="A marsh is a wet place with soft ground, shallow water, and lots of reeds or grasses.",
        ),
        QAItem(
            question="What does it mean to cheat?",
            answer="To cheat means to break the rules or use a sneaky trick to win unfairly.",
        ),
        QAItem(
            question="What is a bloom?",
            answer="A bloom is a flower, often fresh and open, like a little burst of color.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, play together, and try to be kind.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="marsh", challenge="race", name="Mara", gender="girl", friend_name="Bo", friend_gender="boy", trait="tall-talking"),
    StoryParams(place="pond-edge", challenge="stepdance", name="Otis", gender="boy", friend_name="June", friend_gender="girl", trait="plainspoken"),
    StoryParams(place="reedbank", challenge="berrycount", name="Ivy", gender="girl", friend_name="Wade", friend_gender="boy", trait="quick-footed"),
]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for cid, challenge in CHALLENGES.items():
            if reasonableness_gate(place, challenge):
                combos.append((pid, cid))
    return combos


ASP_RULES = r"""
place(P) :- setting(P).
challenge(C) :- contest(C).
valid(P,C) :- setting(P), contest(C), watery(P), blooms(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("setting", pid))
        if place.watery:
            lines.append(asp.fact("watery", pid))
        if place.blooms:
            lines.append(asp.fact("blooms", pid))
    for cid in CHALLENGES:
        lines.append(asp.fact("contest", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(PLACES, params.place),
        _safe_lookup(CHALLENGES, params.challenge),
        params.name,
        params.gender,
        params.friend_name,
        params.friend_gender,
        params.trait,
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
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible place/challenge combos:")
        for p, c in combos:
            print(f"  {p:10} {c}")
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name} and {p.friend_name}: {p.challenge} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
