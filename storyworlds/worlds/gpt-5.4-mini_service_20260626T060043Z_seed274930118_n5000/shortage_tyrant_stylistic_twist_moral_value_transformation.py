#!/usr/bin/env python3
"""
A standalone storyworld for a superhero-style tale about a shortage, a tyrant,
and a stylistic twist that turns into a moral transformation.

Premise:
- A small city depends on glow-cards that power lights, lifts, and little rescue
  gadgets.
- A tyrant is hoarding them during a shortage.
- A young hero wants to stop the hoarding with brave style, but the twist is
  that the only honest victory is to turn the tyrant into a helper, not to
  simply defeat them.

The story is simulated rather than frozen: physical stock changes, public worry
rises and falls, and moral values shift when the hero chooses sharing over
showy force.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0



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
    kind: str = "thing"  # character | thing
    role: str = ""
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    cache_ent: object | None = None
    city_ent: object | None = None
    entities: set[str] = field(default_factory=set)
    hero_ent: object | None = None
    tyrant_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.role in {"hero", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.role in {"heroine", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class City:
    name: str
    setting_line: str
    style_line: str
    shortage_name: str
    shortage_item: str
    power_item: str
    affordance: str
    mood_word: str = "uneasy"
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
class Villain:
    name: str
    title: str
    style: str
    hoard_word: str
    boast: str
    twist_hint: str
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
class Hero:
    name: str
    role: str
    style: str
    moral_word: str
    signature_move: str
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
class StoryParams:
    city: str
    hero_name: str
    hero_role: str
    villain_name: str
    seed: Optional[int] = None
    params: object | None = None
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


class World:
    def __init__(self, city: City, hero: Hero, villain: Villain):
        self.city = city
        self.hero = hero
        self.villain = villain
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        w = World(self.city, self.hero, self.villain)
        w.entities = {k: Entity(**asdict(v)) for k, v in self.entities.items()}
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

CITIES = {
    "skyport": City(
        name="Skyport",
        setting_line="Skyport had tall silver towers, bright windows, and rescue rails that hummed at night.",
        style_line="The whole city liked clean capes, bold colors, and dramatic rooftop leaps.",
        shortage_name="glow-card shortage",
        shortage_item="glow-cards",
        power_item="glow-cards",
        affordance="lights",
        mood_word="dim",
    ),
    "harbor": City(
        name="Harborlight",
        setting_line="Harborlight sat beside the water, with cranes, bridges, and lanterns along the docks.",
        style_line="Its heroes wore flashy masks and made every save look like a comic panel come alive.",
        shortage_name="spark-fuel shortage",
        shortage_item="spark-fuel",
        power_item="spark-fuel",
        affordance="signals",
        mood_word="wary",
    ),
    "metro": City(
        name="Metrovale",
        setting_line="Metrovale was full of buses, subways, and little rooftop gardens between the streets.",
        style_line="The city loved polished boots, bright lightning symbols, and grand speeches from the brave.",
        shortage_name="charge-chip shortage",
        shortage_item="charge-chips",
        power_item="charge-chips",
        affordance="elevators",
        mood_word="stressed",
    ),
}

HEROES = {
    "Ari": Hero(name="Ari", role="hero", style="flashy", moral_word="fairness", signature_move="the Beacon Spin"),
    "Mina": Hero(name="Mina", role="heroine", style="bold", moral_word="sharing", signature_move="the Lantern Leap"),
    "Jace": Hero(name="Jace", role="hero", style="sleek", moral_word="honesty", signature_move="the Sky Arc"),
    "Nia": Hero(name="Nia", role="heroine", style="brisk", moral_word="kindness", signature_move="the Pulse Step"),
}

VILLAINS = {
    "Vex": Villain(
        name="Vex",
        title="the Tyrant",
        style="stylistic and cold",
        hoard_word="hoard",
        boast="Only I should shine while the city waits in the dark.",
        twist_hint="Vex cared more about looking powerful than about ruling wisely.",
    ),
    "Crown": Villain(
        name="Crown",
        title="the Tyrant",
        style="grand and glossy",
        hoard_word="pile up",
        boast="If the city wants light, it must kneel for it.",
        twist_hint="Crown used style like armor, but inside was fear.",
    ),
}

# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(city: City, hero: Hero, villain: Villain) -> bool:
    return bool(city.shortage_item and hero.moral_word and villain.title == "the Tyrant")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for c in CITIES:
        for h in HEROES:
            for v in VILLAINS:
                combos.append((c, h, v))
    return combos


def explain_rejection() -> str:
    return "(No story: the chosen setup does not contain a shortage, a tyrant, and a hero who can answer with a moral turn.)"


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------

def forecast_shortage(world: World) -> dict:
    city = world.get("city")
    cache = world.get("cache")
    tyrant = world.get("tyrant")
    hero = world.get("hero")

    future = world.copy()
    future.get("cache").meters["stock"] -= 2
    future.get("city").meters["worry"] += 1
    future.get("tyrant").memes["greed"] += 1
    future.get("hero").memes["resolve"] += 1

    return {
        "stock_after_hoard": future.get("cache").meters["stock"],
        "worry": future.get("city").meters["worry"],
        "greed": future.get("tyrant").memes["greed"],
        "resolve": future.get("hero").memes["resolve"],
    }


def introduce(world: World) -> None:
    city = world.city
    hero = world.get("hero")
    tyrant = world.get("tyrant")
    cache = world.get("cache")

    world.say(
        f"In {city.name}, {city.setting_line} {city.style_line}"
    )
    world.say(
        f"But the city had a {city.shortage_name}, so the {city.shortage_item} in the vault were precious."
    )
    hero.memes["curiosity"] += 1
    tyrant.memes["greed"] += 1
    world.say(
        f"{hero.id} was a young superhero who loved {hero.moral_word} and bright plans. "
        f"{tyrant.id}, {tyrant.label}, bragged, \"{tyrant.phrase}\""
    )
    world.say(
        f"Every night, the vault held the last {cache.phrase}, and people looked at the dark streets with worried faces."
    )


def raise_tension(world: World) -> None:
    hero = world.get("hero")
    tyrant = world.get("tyrant")
    city = world.get("city")
    cache = world.get("cache")

    forecast = forecast_shortage(world)
    city.meters["worry"] += 1
    cache.meters["stock"] -= 2
    tyrant.meters["hoard"] += 2
    hero.memes["resolve"] += 1

    world.para()
    world.say(
        f"One night, {tyrant.id} grabbed the vault key and hid more {city.shortage_item} behind a steel door."
    )
    world.say(
        f"The shortage got worse: the last stock dropped to {cache.meters['stock']:.0f}, and the city grew {city.mood_word}."
    )
    world.say(
        f"{hero.id} watched the numbers fall and felt {hero.moral_word} tug at {hero.pronoun('possessive')} heart."
    )
    world.say(
        f"{tyrant.id} boomed, \"{tyrant.boast}\""
    )
    world.facts["forecast"] = forecast


def twist_and_transform(world: World) -> None:
    hero = world.get("hero")
    tyrant = world.get("tyrant")
    city = world.get("city")
    cache = world.get("cache")

    world.para()
    hero.memes["style"] += 1
    hero.meters["speed"] += 1
    tyrant.memes["fear"] += 1
    world.say(
        f"{hero.id} did not storm in with a roar. Instead, {hero.pronoun('subject')} used {hero.style} style and struck a pose on the tower rail."
    )
    world.say(
        f"With {hero.signature_move}, {hero.id} flashed a reflected map of the city and showed how the shortage was hurting children, nurses, and train drivers."
    )
    world.say(
        f"That was the twist: {tyrant.id} was not strongest when {tyrant.pronoun('subject')} hoarded power; {tyrant.pronoun('subject')} only looked strong."
    )
    world.say(
        f"{hero.id} said, \"Real strength is making sure everyone gets enough.\""
    )
    world.say(
        f"At first {tyrant.id} sneered, but then {tyrant.pronoun('subject')} saw the dark streets and the people waiting below."
    )
    tyrant.memes["shame"] += 1
    tyrant.memes["humility"] += 1
    tyrant.memes["greed"] = max(0.0, tyrant.memes["greed"] - 1)
    tyrant.meters["hoard"] = max(0.0, tyrant.meters["hoard"] - 1)
    cache.meters["stock"] += 1
    city.meters["worry"] = max(0.0, city.meters["worry"] - 1)


def resolve(world: World) -> None:
    hero = world.get("hero")
    tyrant = world.get("tyrant")
    city = world.city
    cache = world.get("cache")

    world.para()
    hero.memes["joy"] += 1
    hero.memes["resolve"] += 1
    tyrant.memes["service"] += 1
    tyrant.role = "redeemed"
    cache.meters["stock"] += 2
    city.meters["worry"] = 0

    world.say(
        f"{tyrant.id} opened the vault and began handing out {city.shortage_item} to the hospitals, buses, and homes that needed them most."
    )
    world.say(
        f"The city lights blinked awake again. Children cheered, and the rooftops looked gold instead of gray."
    )
    world.say(
        f"{hero.id} stood in the glow, and {hero.pronoun('subject')} knew the real victory was not just stopping a tyrant but changing what power meant."
    )
    world.say(
        f"By morning, {tyrant.id} was no longer hoarding the last {city.power_item}; {tyrant.pronoun('subject')} was helping carry them out, one careful crate at a time."
    )


def tell_story(city: City, hero: Hero, villain: Villain) -> World:
    world = World(city, hero, villain)
    hero_ent = world.add(Entity(id=hero.name, kind="character", role=hero.role, label="hero"))
    tyrant_ent = world.add(Entity(id=villain.name, kind="character", role="tyrant", label=villain.title, phrase=villain.boast))
    city_ent = world.add(Entity(id="city", kind="thing", label=city.name, phrase=city.shortage_name))
    cache_ent = world.add(Entity(id="cache", kind="thing", label="vault cache", phrase=city.shortage_item, meters={"stock": 3}))
    world.facts.update(hero=hero_ent, tyrant=tyrant_ent, city=city, cache=cache_ent)
    introduce(world)
    raise_tension(world)
    twist_and_transform(world)
    resolve(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    c = world.city
    h = world.hero
    v = world.villain
    return [
        f"Write a short superhero story about a {c.shortage_name} in {c.name} and a {v.title} who hoards the last {c.shortage_item}.",
        f"Tell a child-friendly adventure where {h.name} uses {h.style} style, then learns a moral lesson about {h.moral_word}.",
        f"Write a story with a twist where a tyrant seems mighty, but the real transformation is that power gets shared.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h = world.get("hero")
    v = world.get("tyrant")
    c = world.city
    cache = world.get("cache")
    return [
        QAItem(
            question=f"What shortage was troubling {c.name}?",
            answer=f"{c.name} had a {c.shortage_name}, so everyone worried about the last {c.shortage_item} in the vault.",
        ),
        QAItem(
            question=f"What did {v.id} do that made the problem worse?",
            answer=f"{v.id}, {v.label}, hoarded the vault cache and tried to keep the last {c.shortage_item} away from everyone else.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {v.id} only looked powerful while hoarding. When {h.name} showed the damage, {v.id} became humble and started helping share the {c.shortage_item}.",
        ),
        QAItem(
            question=f"How did {h.name} win without acting like a bully?",
            answer=f"{h.name} used {h.style} style, showed the truth, and chose {h.moral_word} over a loud fight. That helped turn the tyrant toward the right thing.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"The vault opened, the {c.shortage_item} were shared, the city lights came back, and {v.id} was transformed from a hoarder into a helper.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    c = world.city
    return [
        QAItem(
            question="What is a tyrant?",
            answer="A tyrant is a ruler who uses power unfairly and controls others by force or fear.",
        ),
        QAItem(
            question="What is a shortage?",
            answer="A shortage is when there is not enough of something people need.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into a new kind of state, like a selfish person becoming kind.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is an important idea about how to treat people, such as fairness, kindness, or honesty.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/3.
city(C) :- city_fact(C).
hero(H) :- hero_fact(H).
villain(V) :- villain_fact(V).

valid(C,H,V) :- city(C), hero(H), villain(V).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for cid in CITIES:
        lines.append(asp.fact("city_fact", cid))
    for hid in HEROES:
        lines.append(asp.fact("hero_fact", hid))
    for vid in VILLAINS:
        lines.append(asp.fact("villain_fact", vid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(""))
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero-style storyworld: a shortage, a tyrant, and a moral twist."
    )
    ap.add_argument("--city", choices=CITIES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--villain", choices=VILLAINS)
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
    city = getattr(args, "city", None) or rng.choice(list(CITIES))
    hero = getattr(args, "hero", None) or rng.choice(list(HEROES))
    villain = getattr(args, "villain", None) or rng.choice(list(VILLAINS))
    if not valid_combo(_safe_lookup(CITIES, city), _safe_lookup(HEROES, hero), _safe_lookup(VILLAINS, villain)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(city=city, hero_name=hero, hero_role=_safe_lookup(HEROES, hero).role, villain_name=villain, seed=getattr(args, "seed", None))


def generate(params: StoryParams) -> StorySample:
    city = _safe_lookup(CITIES, params.city)
    hero = _safe_lookup(HEROES, params.hero_name)
    villain = _safe_lookup(VILLAINS, params.villain_name)
    world = tell_story(city, hero, villain)
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
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for city in CITIES:
            for hero in HEROES:
                for villain in VILLAINS:
                    try:
                        params = StoryParams(city=city, hero_name=hero, hero_role=_safe_lookup(HEROES, hero).role, villain_name=villain, seed=base_seed)
                        samples.append(generate(params))
                    except StoryError:
                        pass
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 40, 40):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
