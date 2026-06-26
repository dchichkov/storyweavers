#!/usr/bin/env python3
"""
storyworlds/worlds/sport_captive_foreshadowing_mystery_to_solve_fable.py
========================================================================

A small fable-like storyworld about a sport, a captive, and a clue trail that
turns into a mystery to solve.

The domain is intentionally compact:
- a young animal hero loves a sport,
- a captive creature is in trouble nearby,
- foreshadowing clues appear during the sport,
- the hero solves the mystery and frees the captive,
- the ending carries a simple fable moral.

The world is state-driven rather than template-swapped: meters and memes change
through the beats, and the clues determine the resolution.
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
    captive_of: Optional[str] = None
    freed: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "doe", "hen", "cow"}
        male = {"boy", "father", "dad", "man", "buck", "rooster", "bull"}
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
    outdoor: bool = True
    surface: str = "grass"
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
class Sport:
    id: str
    name: str
    verb: str
    gerund: str
    clue: str
    clue_kind: str
    zone: set[str]
    noise: str
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
class Captive:
    id: str
    label: str
    phrase: str
    type: str
    location: str
    danger: str
    needs: str
    tags: set[str] = field(default_factory=set)
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
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    helps: set[str]
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.clues: list[str] = []
        self.riddle_answer: str = ""

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SPORTS = {
    "racing": Sport(
        id="racing",
        name="a footrace",
        verb="run in the race",
        gerund="racing across the meadow",
        clue="a line of bent grass",
        clue_kind="grass",
        zone={"path"},
        noise="soft thumps of paws",
        tags={"sport", "race"},
    ),
    "ball": Sport(
        id="ball",
        name="a ball game",
        verb="chase the ball",
        gerund="playing with the ball",
        clue="a scuffed ball print",
        clue_kind="print",
        zone={"field"},
        noise="bouncy taps",
        tags={"sport", "ball"},
    ),
    "hoops": Sport(
        id="hoops",
        name="a hoop game",
        verb="throw the ring through the hoop",
        gerund="tossing rings",
        clue="a bright ring snagged on a twig",
        clue_kind="ring",
        zone={"courtyard"},
        noise="little clinks",
        tags={"sport", "ring"},
    ),
}

CAPTIVES = {
    "swallow": Captive(
        id="swallow",
        label="swallow",
        phrase="a small swallow in a wicker cage",
        type="bird",
        location="the old gate",
        danger="the latch had stuck shut",
        needs="the key",
        tags={"captive", "bird"},
    ),
    "mouse": Captive(
        id="mouse",
        label="mouse",
        phrase="a tiny mouse in a woven basket",
        type="mouse",
        location="the shed corner",
        danger="the door had been tied tight",
        needs="the knot cutter",
        tags={"captive", "mouse"},
    ),
    "kid": Captive(
        id="kid",
        label="kid",
        phrase="a little goat kid behind a pen door",
        type="goat",
        location="the stone pen",
        danger="the bolt had slid into place",
        needs="the bolt stick",
        tags={"captive", "goat"},
    ),
}

TOOLS = {
    "key": Tool(
        id="key",
        label="a small brass key",
        phrase="a small brass key",
        use="open the cage",
        helps={"swallow"},
    ),
    "cutter": Tool(
        id="cutter",
        label="a sharp little cutter",
        phrase="a sharp little cutter",
        use="slice the knot",
        helps={"mouse"},
    ),
    "stick": Tool(
        id="stick",
        label="a smooth bolt stick",
        phrase="a smooth bolt stick",
        use="lift the bolt",
        helps={"kid"},
    ),
}

HERO_NAMES = ["Milo", "Pip", "Nia", "Rory", "Tala", "Bram", "Luna", "Otto"]
HERO_TYPES = ["hare", "fox", "mouse", "squirrel", "rabbit"]
TRAITS = ["curious", "gentle", "quick", "brave", "careful", "bright"]


@dataclass
class StoryParams:
    setting: str
    sport: str
    captive: str
    hero_name: str
    hero_type: str
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


def setup_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    world = World(setting)
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        meters={"energy": 2.0, "balance": 1.0},
        memes={"joy": 1.0, "curiosity": 1.0},
    ))
    captive = _safe_lookup(CAPTIVES, params.captive)
    world.add(Entity(
        id=captive.id,
        kind="character",
        type=captive.type,
        label=captive.label,
        phrase=captive.phrase,
        caretaker="keeper",
        captive_of="keeper",
        meters={"worry": 2.0},
        memes={"hope": 0.5, "fear": 2.0},
    ))
    world.add(Entity(
        id="keeper",
        kind="character",
        type="fox",
        label="the keeper",
        meters={"busy": 1.0},
        memes={"pride": 1.0, "care": 0.5},
    ))
    world.add(Entity(
        id="tool",
        type=_safe_lookup(TOOLS, captive.needs.replace("the ", "").replace("a ", "").replace("an ", "")).id,
        label=_safe_lookup(TOOLS, captive.needs.replace("the ", "").replace("a ", "").replace("an ", "")).label,
    ))
    return world


SETTINGS = {
    "meadow": Setting(place="the meadow", outdoor=True, surface="grass"),
    "courtyard": Setting(place="the courtyard", outdoor=True, surface="stone"),
    "riverbank": Setting(place="the riverbank", outdoor=True, surface="sand"),
}


def reasonableness_gate(sport: Sport, captive: Captive) -> bool:
    if captive.id == "swallow" and sport.id in {"racing", "ball", "hoops"}:
        return True
    if captive.id == "mouse" and sport.id in {"ball", "hoops"}:
        return True
    if captive.id == "kid" and sport.id in {"racing", "ball"}:
        return True
    return False


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for setting in SETTINGS:
        for sport_id in SPORTS:
            for captive_id in CAPTIVES:
                if reasonableness_gate(_safe_lookup(SPORTS, sport_id), _safe_lookup(CAPTIVES, captive_id)):
                    out.append((sport_id, captive_id))
    return out


def _sport_step(world: World, hero: Entity, sport: Sport, captive: Captive) -> None:
    hero.meters["energy"] = hero.meter("energy") - 0.5
    hero.memes["joy"] = hero.meme("joy") + 0.5
    hero.memes["curiosity"] = hero.meme("curiosity") + 0.5
    world.clues.append(sport.clue)
    world.say(
        f"{hero.id} loved {sport.gerund}; the little {sport.noise} made the day feel bright."
    )
    world.say(
        f"But beside {world.setting.place}, {captive.phrase} waited quietly, and "
        f"something about the scene did not fit."
    )


def _foreshadow(world: World, hero: Entity, sport: Sport, captive: Captive) -> None:
    world.say(
        f"{hero.id} noticed {sport.clue}, then saw {captive.danger} near {captive.location}."
    )
    world.say(
        f"That was the first clue, and {hero.id}'s heart turned careful."
    )
    hero.memes["worry"] = hero.meme("worry") + 1.0
    if captive.id == "swallow":
        world.riddle_answer = "the key"
    elif captive.id == "mouse":
        world.riddle_answer = "the cutter"
    else:
        world.riddle_answer = "the stick"


def _mystery_turn(world: World, hero: Entity, sport: Sport, captive: Captive) -> None:
    world.say(
        f"{hero.id} followed the clues: first the {sport.clue_kind}, then the locked place, "
        f"then the missing tool."
    )
    world.say(
        f"It was a small mystery to solve, and the answer was hidden in plain sight."
    )
    hero.memes["curiosity"] = hero.meme("curiosity") + 1.0
    hero.memes["hope"] = hero.meme("hope") + 1.0


def _solve(world: World, hero: Entity, captive: Captive, sport: Sport) -> None:
    tool_key = captive.needs.replace("the ", "").replace("a ", "").replace("an ", "")
    tool = _safe_lookup(TOOLS, tool_key)
    world.say(
        f"{hero.id} found {tool.phrase} by the edge of the field, just where the last clue had led."
    )
    world.say(
        f"With {tool.label}, {hero.id} could {tool.use}."
    )
    captive_ent = world.get(captive.id)
    captive_ent.freed = True
    captive_ent.meters["worry"] = 0.0
    captive_ent.memes["fear"] = 0.0
    captive_ent.memes["hope"] = captive_ent.meme("hope") + 2.0
    world.facts["tool"] = tool
    world.facts["solved"] = True


def _ending(world: World, hero: Entity, captive: Captive) -> None:
    world.say(
        f"The captive {captive.label} blinked, stepped free, and the meadow felt wider at once."
    )
    world.say(
        f"{hero.id} smiled, and even the keeper looked less proud and more wise."
    )
    world.say("The fable's lesson was simple: a keen eye and a kind heart can open what force cannot.")


def tell_story(params: StoryParams) -> World:
    world = setup_world(params)
    hero = world.get(params.hero_name)
    sport = _safe_lookup(SPORTS, params.sport)
    captive = _safe_lookup(CAPTIVES, params.captive)

    world.say(
        f"Once in {world.setting.place}, there lived a {params.trait} {params.hero_type} named {hero.id}."
    )
    world.say(
        f"{hero.id} loved {sport.name}, but nearby was {captive.phrase}."
    )
    world.para()

    _sport_step(world, hero, sport, captive)
    _foreshadow(world, hero, sport, captive)
    world.para()
    _mystery_turn(world, hero, sport, captive)
    _solve(world, hero, captive, sport)
    world.para()
    _ending(world, hero, captive)

    world.facts.update(
        hero=hero,
        sport=sport,
        captive=captive,
        setting=world.setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    sport = _safe_fact(world, f, "sport")
    captive = _safe_fact(world, f, "captive")
    return [
        f"Write a fable for young children about {hero.id}, a {hero.type} who loves {sport.name}, and a captive {captive.label}.",
        f"Tell a short story with foreshadowing and a mystery to solve where {hero.id} notices clues during {sport.gerund}.",
        f"Write a child-friendly fable in which a sport scene leads to the rescue of {captive.phrase}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    sport = _safe_fact(world, f, "sport")
    captive = _safe_fact(world, f, "captive")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"What did {hero.id} love to do in the story?",
            answer=f"{hero.id} loved {sport.name}, especially {sport.gerund}.",
        ),
        QAItem(
            question=f"What was the mystery that {hero.id} had to solve?",
            answer=f"{hero.id} had to solve how to free the captive {captive.label} by finding {tool.label}.",
        ),
        QAItem(
            question=f"What clue first made {hero.id} stop and look more closely?",
            answer=f"The first clue was {sport.clue}, which helped {hero.id} notice that something was wrong.",
        ),
        QAItem(
            question=f"How did the story end for the captive {captive.label}?",
            answer=f"The captive {captive.label} was freed, and the meadow felt open and peaceful again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    sport = _safe_fact(world, f, "sport")
    captive = _safe_fact(world, f, "captive")
    items = [
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story leaves small clues early so readers can guess what may happen later.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a problem or secret that people have to think about and solve.",
        ),
        QAItem(
            question="What does a captive mean?",
            answer="A captive is someone or something that is kept from going free.",
        ),
        QAItem(
            question="Why do fables often teach lessons?",
            answer="Fables use simple animal stories to show a lesson about how to act wisely and kindly.",
        ),
    ]
    if sport.id == "racing":
        items.append(QAItem(
            question="What is a race in sports?",
            answer="A race is a sport where runners try to move quickly from one place to another.",
        ))
    if captive.id == "swallow":
        items.append(QAItem(
            question="What is a cage for?",
            answer="A cage is a enclosure that keeps an animal from going free.",
        ))
    return items


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
        if e.freed:
            bits.append("freed=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  clues: {world.clues}")
    return "\n".join(lines)


ASP_RULES = r"""
sport_sport(ball).
sport_sport(racing).
sport_sport(hoops).

captive_kind(swallow).
captive_kind(mouse).
captive_kind(kid).

valid_combo(S, C) :- sport_sport(S), captive_kind(C), ok(S, C).

ok(racing, swallow).
ok(ball, swallow).
ok(hoops, swallow).

ok(ball, mouse).
ok(hoops, mouse).

ok(racing, kid).
ok(ball, kid).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SPORTS:
        lines.append(asp.fact("sport_sport", sid))
    for cid in CAPTIVES:
        lines.append(asp.fact("captive_kind", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


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
    ap = argparse.ArgumentParser(
        description="A fable-like storyworld about sport, captive, foreshadowing, and a mystery to solve."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--sport", choices=SPORTS)
    ap.add_argument("--captive", choices=CAPTIVES)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
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
    combos = valid_combos()
    filtered = [
        (s, c) for s, c in combos
        if (getattr(args, "sport", None) is None or s == getattr(args, "sport", None))
        and (getattr(args, "captive", None) is None or c == getattr(args, "captive", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    sport, captive = rng.choice(list(filtered))
    setting = getattr(args, "setting", None) or rng.choice(sorted(SETTINGS))
    if getattr(args, "sport", None) and getattr(args, "captive", None) and not reasonableness_gate(_safe_lookup(SPORTS, getattr(args, "sport", None)), _safe_lookup(CAPTIVES, getattr(args, "captive", None))):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        sport=sport,
        captive=captive,
        hero_name=name,
        hero_type=hero_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
    StoryParams(setting="meadow", sport="racing", captive="swallow", hero_name="Milo", hero_type="hare", trait="curious"),
    StoryParams(setting="courtyard", sport="ball", captive="mouse", hero_name="Pip", hero_type="fox", trait="careful"),
    StoryParams(setting="riverbank", sport="hoops", captive="kid", hero_name="Tala", hero_type="rabbit", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_combo/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible sport/captive combos:")
        for s, c in combos:
            print(f"  {s} / {c}")
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
            header = f"### {p.hero_name}: {p.sport} / {p.captive}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
