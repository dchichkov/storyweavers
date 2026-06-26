#!/usr/bin/env python3
"""
A standalone story world for a small mystery about a tutor, a campaign, and
a curious act of sharing that leads to a bad ending.

The world is built around a tiny school campaign:
- a tutor organizes a curiosity campaign to gather clues,
- children share notes and objects,
- one choice is too trusting,
- the final reveal proves that curiosity and sharing can uncover truth,
  but also cause a bad ending for the group when the wrong person gets the clue.

This file follows the Storyweavers storyworld contract:
- self-contained stdlib script
- imports shared results eagerly
- imports shared asp lazily inside ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    prize: object | None = None
    tutor: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "tutor"}
        male = {"boy", "father", "dad", "man", "dear"}
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
class Place:
    id: str
    name: str
    indoor: bool
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
class Campaign:
    id: str
    label: str
    theme: str
    method: str
    clue: str
    risk: str
    ending: str
    target_role: str
    tags: set[str] = field(default_factory=set)
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
class Guard:
    id: str
    label: str
    covers: set[str]
    prevents: set[str]
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    place: str
    campaign: str
    prize: str
    protagonist: str
    role: str
    tutor: str
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


PLACES = {
    "library": Place("library", "the library", True, {"curiosity", "sharing", "search"}),
    "hall": Place("hall", "the school hall", True, {"curiosity", "sharing", "search"}),
    "garden": Place("garden", "the garden path", False, {"curiosity", "sharing", "search"}),
    "museum": Place("museum", "the museum room", True, {"curiosity", "sharing", "search"}),
}

CAMPAIGNS = {
    "curiosity": Campaign(
        id="curiosity",
        label="Curiosity Campaign",
        theme="curiosity",
        method="look for clues",
        clue="a small hidden note",
        risk="too curious",
        ending="the clue vanished into the wrong hands",
        target_role="tutor",
        tags={"curiosity", "mystery"},
    ),
    "sharing": Campaign(
        id="sharing",
        label="Sharing Campaign",
        theme="sharing",
        method="pass clues from hand to hand",
        clue="a shared ribbon marker",
        risk="too trusting",
        ending="the ribbon was shared with a thief",
        target_role="tutor",
        tags={"sharing", "mystery"},
    ),
    "bad_ending": Campaign(
        id="bad_ending",
        label="Bad Ending Campaign",
        theme="bad ending",
        method="follow the last message",
        clue="a torn page with a warning",
        risk="not careful enough",
        ending="the warning came too late",
        target_role="tutor",
        tags={"bad ending", "mystery"},
    ),
}

PRIZES = {
    "letter": Prize("letter", "a sealed letter", "hands"),
    "notebook": Prize("notebook", "a little notebook", "hands"),
    "key": Prize("key", "an old brass key", "hands"),
    "lantern": Prize("lantern", "a small lantern", "hands"),
}

GUARDS = [
    Guard(
        id="gloves",
        label="soft gloves",
        covers={"hands"},
        prevents={"wet ink", "sticky dust"},
        prep="put on soft gloves first",
        tail="then followed the clue trail carefully",
    ),
    Guard(
        id="bag",
        label="a paper bag",
        covers={"hands"},
        prevents={"stolen clue"},
        prep="carry the clue in a paper bag",
        tail="kept the clue out of the wrong hands",
    ),
    Guard(
        id="lamp",
        label="a small lamp",
        covers={"hands"},
        prevents={"darkness"},
        prep="bring a small lamp",
        tail="shone light on the hidden corner",
    ),
]

GIRL_NAMES = ["Mina", "Lena", "Ivy", "Nora", "Tess", "Ava"]
BOY_NAMES = ["Eli", "Noah", "Theo", "Finn", "Otto", "Jude"]
TUTOR_NAMES = ["Ms. Vale", "Mr. Lane", "Tutor June", "Tutor Reed"]
TRAITS = ["curious", "careful", "quiet", "brave", "restless"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for camp_id in place.affords:
            for prize_id in PRIZES:
                combos.append((place_id, camp_id, prize_id))
    return combos


def reason_invalid(place: Place, camp: Campaign, prize: Prize) -> str:
    return (
        f"(No story: the {camp.label} does not fit a prize worn on the {prize.region}, "
        f"or the place cannot support that kind of clue hunt.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery story world about a tutor, a campaign, and a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--campaign", choices=CAMPAIGNS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["girl", "boy"])
    ap.add_argument("--tutor", choices=TUTOR_NAMES)
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
    if getattr(args, "campaign", None):
        combos = [c for c in combos if c[1] == getattr(args, "campaign", None)]
    if getattr(args, "prize", None):
        combos = [c for c in combos if c[2] == getattr(args, "prize", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place_id, camp_id, prize_id = rng.choice(list(combos))
    role = getattr(args, "role", None) or rng.choice(["girl", "boy"])
    prize = _safe_lookup(PRIZES, prize_id)
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if role == "girl" else BOY_NAMES)
    tutor = getattr(args, "tutor", None) or rng.choice(TUTOR_NAMES)
    return StoryParams(place=place_id, campaign=camp_id, prize=prize_id, protagonist=name, role=role, tutor=tutor)


def _activity_line(camp: Campaign) -> str:
    return {
        "curiosity": "The room felt full of hush and questions.",
        "sharing": "Every desk had a note, and every note seemed to want to travel.",
        "bad ending": "The hallway felt like a place where one wrong step could spoil everything.",
    }[camp.theme]


def _predict(world: World, hero: Entity, camp: Campaign, prize: Entity) -> dict:
    sim = world.copy()
    hero_sim = sim.get(hero.id)
    hero_sim.memes["curiosity"] = hero_sim.memes.get("curiosity", 0) + 1
    hero_sim.memes["sharing"] = hero_sim.memes.get("sharing", 0) + 1
    if camp.id == "sharing":
        prize_sim = sim.get(prize.id)
        prize_sim.meters["lost"] = prize_sim.meters.get("lost", 0) + 1
    return {"lost": sim.get(prize.id).meters.get("lost", 0) >= THRESHOLD}


def _do_campaign(world: World, hero: Entity, camp: Campaign, prize: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(f"{hero.id} leaned in, because {camp.theme} always made questions feel bigger.")
    world.say(_activity_line(camp))
    if camp.id == "sharing":
        prize.meters["shared"] = prize.meters.get("shared", 0) + 1
        world.say(f"{hero.id} shared {prize.phrase} with the group, thinking it would help the search.")
    elif camp.id == "curiosity":
        prize.meters["examined"] = prize.meters.get("examined", 0) + 1
        world.say(f"{hero.id} carefully examined {prize.phrase} and noticed a tiny mark near the edge.")
    else:
        prize.meters["warned"] = prize.meters.get("warned", 0) + 1
        world.say(f"{hero.id} followed the torn page, but the warning at the bottom looked almost too late.")


def _gear_for(camp: Campaign, prize: Prize) -> Optional[Guard]:
    for g in GUARDS:
        if prize.region in g.covers:
            return g
    return None


def tell(place: Place, camp: Campaign, prize_cfg: Prize, hero_name: str, role: str, tutor_name: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=role, role="student"))
    tutor = world.add(Entity(id="Tutor", kind="character", type="tutor", label=tutor_name, role="tutor"))
    prize = world.add(Entity(id="Prize", type=prize_cfg.label, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id))
    hero.memes["curiosity"] = 0
    tutor.memes["worry"] = 0

    world.say(f"Dear {tutor.label}, the campaign began with a whisper and a promise to look closer.")
    world.say(f"{hero.id} was a {role} who liked mysteries, and {tutor.label} watched the class with a careful eye.")
    world.say(f"They were in {place.name}, where every corner seemed ready to hide a clue.")
    world.para()
    world.say(f"The {camp.label.lower()} asked everyone to {camp.method}.")
    world.say(f"{hero.id} felt especially {camp.theme}, and {hero.id} wanted to solve the little puzzle before anyone else.")
    world.say(f"{tutor.label} held up {prize.phrase} and said it mattered because one missing detail could change the whole result.")
    if _predict(world, hero, camp, prize)["lost"]:
        tutor.memes["worry"] += 1
        world.say(f'"If we are not careful, {camp.ending}," {tutor.label} said.')
    world.para()
    _do_campaign(world, hero, camp, prize)
    if camp.id == "sharing":
        prize.meters["lost"] = 1
        world.say(f"Then the clue slipped away, and the wrong child carried it out of sight.")
    elif camp.id == "curiosity":
        world.say(f"At last, the tiny mark led them to a hidden drawer, but the answer inside was not kind.")
        prize.meters["found"] = 1
        tutor.memes["sadness"] += 1
        world.say(f"The missing note named the culprit, but it also meant the campaign had already gone wrong.")
    else:
        prize.meters["warned"] = 1
        tutor.memes["sadness"] += 1
        world.say(f"The last message was true, but it came after the trail was spoiled.")
    world.para()
    guard = _gear_for(camp, prize_cfg)
    if guard:
        world.say(f"{tutor.label} tried one safer plan: {guard.prep}.")
        world.say(f"That choice {guard.tail}, yet the day still ended badly because the clue had already been lost.")
    world.say(f"In the end, {hero.id} stood very still, because curiosity had helped solve the mystery and sharing had also made the loss worse.")
    world.say(f"The class went home with an empty hand and a heavy feeling, while {tutor.label} kept the last torn page for tomorrow.")
    world.facts.update(hero=hero, tutor=tutor, prize=prize, place=place, campaign=camp, guard=guard)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(CAMPAIGNS, params.campaign), _safe_lookup(PRIZES, params.prize), params.protagonist, params.role, params.tutor)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    camp = _safe_fact(world, f, "campaign")
    tutor = _safe_fact(world, f, "tutor")
    return [
        f"Write a short mystery for a child about {hero.id}, {tutor.label}, and a {camp.theme} campaign.",
        f"Tell a gentle story where {hero.id} is curious, sharing causes trouble, and the ending is bad.",
        f"Write a school mystery with a tutor, a campaign, and one clue that is shared too far.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    tutor = _safe_fact(world, f, "tutor")
    camp = _safe_fact(world, f, "campaign")
    qa = [
        QAItem(
            question=f"Who was the story mainly about?",
            answer=f"It was about {hero.id}, a {hero.type} who got caught up in the {camp.label.lower()}.",
        ),
        QAItem(
            question=f"Why did {tutor.label} worry during the campaign?",
            answer=f"{tutor.label} worried because the clue could be lost if {hero.id} was too curious or shared it with the wrong person.",
        ),
        QAItem(
            question=f"What made the ending bad?",
            answer=f"The ending was bad because the clue slipped away, so the class lost what they needed to finish the mystery well.",
        ),
    ]
    if camp.id == "sharing":
        qa.append(QAItem(
            question="What happened when the class shared the clue?",
            answer="The clue was passed around, and then it ended up in the wrong hands, which made the result go badly.",
        ))
    return qa


WORLD_QA = {
    "curiosity": [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to look, ask, and find out more about something.",
        )
    ],
    "sharing": [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use, see, or hold something for a while.",
        )
    ],
    "mystery": [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle or secret that people try to solve by looking for clues.",
        )
    ],
    "tutor": [
        QAItem(
            question="What does a tutor do?",
            answer="A tutor helps people learn by explaining, asking questions, and guiding them carefully.",
        )
    ],
    "bad ending": [
        QAItem(
            question="What is a bad ending in a story?",
            answer="A bad ending is when things turn out poorly or the problem is not solved in a happy way.",
        )
    ],
}


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = []
    out.extend(WORLD_QA["curiosity"])
    out.extend(WORLD_QA["sharing"])
    out.extend(WORLD_QA["mystery"])
    out.extend(WORLD_QA["tutor"])
    out.extend(WORLD_QA["bad ending"])
    return out


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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"place={world.place.name}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="library", campaign="curiosity", prize="letter", protagonist="Mina", role="girl", tutor="Tutor June"),
    StoryParams(place="hall", campaign="sharing", prize="notebook", protagonist="Eli", role="boy", tutor="Ms. Vale"),
    StoryParams(place="museum", campaign="bad_ending", prize="key", protagonist="Nora", role="girl", tutor="Mr. Lane"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoor:
            lines.append(asp.fact("indoor", pid))
        for c in sorted(place.affords):
            lines.append(asp.fact("affords", pid, c))
    for cid, camp in CAMPAIGNS.items():
        lines.append(asp.fact("campaign", cid))
        lines.append(asp.fact("theme", cid, camp.theme))
    for prid, prize in PRIZES.items():
        lines.append(asp.fact("prize", prid))
        lines.append(asp.fact("worn_on", prid, prize.region))
    for gid, g in enumerate(GUARDS):
        lines.append(asp.fact("guard", g.id))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Camp, Prize) :- place(Place), campaign(Camp), prize(Prize), affords(Place, Camp), prize_worn_on(Prize, _).
valid_story(Place, Camp, Prize) :- valid(Place, Camp, Prize).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python = set(valid_combos())
    clingo = set(asp_valid_combos())
    if python == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(python)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if python - clingo:
        print("  only in python:", sorted(python - clingo))
    if clingo - python:
        print("  only in clingo:", sorted(clingo - python))
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print("  ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
            header = f"### {p.protagonist}: {p.campaign} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
