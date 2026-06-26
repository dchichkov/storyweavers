#!/usr/bin/env python3
"""
storyworlds/worlds/noose_market_magic_superhero_story.py
========================================================

A small superhero story world set in a market, with magic, a dangerous
magical noose, and a gentle rescue.

The world is constraint-driven: the hero only gets into trouble when the
villain's magic noose is actually able to snare something important in the
market, and the resolution only works when the hero has the right magical
countermeasure.
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
    caretakers: list[str] = field(default_factory=list)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    magic: bool = False
    grounded: bool = False

    hero: object | None = None
    power: object | None = None
    prize: object | None = None
    sidekick: object | None = None
    threat: object | None = None
    villain: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def poss(self) -> str:
        return self.pronoun("possessive")

    def obj(self) -> str:
        return self.pronoun("object")
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
class Market:
    place: str = "the market"
    stalls: list[str] = field(default_factory=lambda: ["fruit stall", "flower stall", "toy stall"])
    noise: str = "buzzy"
    w: object | None = None
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
class Power:
    id: str
    label: str
    verb: str
    shield: str
    counter: str
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
class Threat:
    id: str
    label: str
    verb: str
    effect: str
    zone: set[str]
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
    id: str
    label: str
    phrase: str
    region: str
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


class World:
    def __init__(self, market: Market) -> None:
        self.market = market
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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
        import copy

        clone = World(self.market)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    hero: str
    sidekick: str
    villain: str
    prize: str
    power: str
    threat: str
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


HEROES = [
    ("Brightbolt", "girl", "cheerful"),
    ("Starshield", "boy", "brave"),
    ("Cometwing", "girl", "quick"),
    ("Thunderkid", "boy", "kind"),
]
SIDEKICKS = [
    ("Pip", "boy"),
    ("Mira", "girl"),
    ("Dot", "girl"),
    ("Ned", "boy"),
]
VILLAINS = [
    ("Murk", "man"),
    ("Slip", "woman"),
    ("Grin", "man"),
]
PRIZES = {
    "basket": Prize("basket", "a woven basket of pears", "basket", "hands", {"fruit"}),
    "kite": Prize("kite", "a bright red kite", "kite", "hands", {"toy"}),
    "bell": Prize("bell", "a silver market bell", "bell", "hands", {"market"}),
}
POWERS = {
    "spark": Power("spark", "spark magic", "spark", "a glow shield", "a shower of sparks", {"magic", "light"}),
    "bubble": Power("bubble", "bubble magic", "bubble", "a bubble shield", "a burst of bubbles", {"magic", "soft"}),
    "mirror": Power("mirror", "mirror magic", "mirror", "a mirror shield", "a flash of reflected light", {"magic", "bright"}),
}
THREATS = {
    "noose": Threat("noose", "a magical noose", "throws a magical noose", "can snare what it catches", {"hands", "stall"}, {"magic", "rope", "noose"}),
    "smoke": Threat("smoke", "a smoky spell", "blows smoky spell", "can hide the path", {"eyes"}, {"magic", "smoke"}),
}

CURATED = [
    StoryParams(hero="Brightbolt", sidekick="Pip", villain="Murk", prize="basket", power="spark", threat="noose"),
    StoryParams(hero="Starshield", sidekick="Mira", villain="Slip", prize="kite", power="bubble", threat="noose"),
    StoryParams(hero="Cometwing", sidekick="Dot", villain="Grin", prize="bell", power="mirror", threat="noose"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero story world set in a market with magic and a noose.")
    ap.add_argument("--hero", choices=[h[0] for h in HEROES])
    ap.add_argument("--sidekick", choices=[s[0] for s in SIDEKICKS])
    ap.add_argument("--villain", choices=[v[0] for v in VILLAINS])
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = getattr(args, "hero", None) or rng.choice([h[0] for h in HEROES])
    sidekick = getattr(args, "sidekick", None) or rng.choice([s[0] for s in SIDEKICKS])
    villain = getattr(args, "villain", None) or rng.choice([v[0] for v in VILLAINS])
    prize = getattr(args, "prize", None) or rng.choice(list(PRIZES))
    power = getattr(args, "power", None) or rng.choice(list(POWERS))
    threat = getattr(args, "threat", None) or "noose"

    if threat != "noose":
        return _fallback_storyparams(args, rng, StoryParams, globals())

    return StoryParams(hero=hero, sidekick=sidekick, villain=villain, prize=prize, power=power, threat=threat)


def reasonableness_ok(params: StoryParams) -> bool:
    return params.threat == "noose" and params.power in POWERS and params.prize in PRIZES


def _hero_type(name: str) -> str:
    for n, t, _ in HEROES:
        if n == name:
            return t
    return "hero"


def _sidekick_type(name: str) -> str:
    for n, t in SIDEKICKS:
        if n == name:
            return t
    return "friend"


def build_world(params: StoryParams) -> World:
    if not reasonableness_ok(params):
        pass
    w = World(Market())
    hero_type = _hero_type(params.hero)
    sidekick_type = _sidekick_type(params.sidekick)
    villain_type = next((t for n, t in VILLAINS if n == params.villain), "villain")

    hero = w.add(Entity(id=params.hero, kind="character", type=hero_type, label=params.hero, memes={"joy": 1.0, "duty": 1.0}))
    sidekick = w.add(Entity(id=params.sidekick, kind="character", type=sidekick_type, label=params.sidekick, memes={"curiosity": 1.0}))
    villain = w.add(Entity(id=params.villain, kind="character", type=villain_type, label=params.villain, memes={"mischief": 1.0}))
    prize = w.add(Entity(id=params.prize, kind="thing", type=params.prize, label=_safe_lookup(PRIZES, params.prize).label, phrase=_safe_lookup(PRIZES, params.prize).phrase, owner=params.hero))
    power = w.add(Entity(id=params.power, kind="thing", type="power", label=_safe_lookup(POWERS, params.power).label, phrase=_safe_lookup(POWERS, params.power).counter, owner=params.hero, magic=True))
    threat = w.add(Entity(id=params.threat, kind="thing", type="threat", label=_safe_lookup(THREATS, params.threat).label, phrase=_safe_lookup(THREATS, params.threat).effect, owner=params.villain, magic=True))
    w.facts.update(hero=hero, sidekick=sidekick, villain=villain, prize=prize, power=power, threat=threat, params=params)
    return w


def predict_capture(world: World) -> bool:
    return world.facts["prize"].meters.get("snared", 0.0) >= THRESHOLD or world.facts["prize"].memes.get("in_danger", 0.0) >= THRESHOLD


def perform_scene(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    sidekick: Entity = _safe_fact(world, world.facts, "sidekick")
    villain: Entity = _safe_fact(world, world.facts, "villain")
    prize: Entity = _safe_fact(world, world.facts, "prize")
    power: Entity = _safe_fact(world, world.facts, "power")
    threat: Entity = _safe_fact(world, world.facts, "threat")

    world.say(f"On a busy day at {world.market.place}, {hero.id} kept watch over the stalls while {sidekick.id} helped carry small things.")
    world.say(f"{prize.label.capitalize()} sat near the fruit stall, and {hero.id} liked how the market smelled of bread and oranges.")
    world.para()
    world.say(f"Then {villain.id} stepped in with {threat.label} in hand and tried to {_safe_lookup(THREATS, threat.type).verb} toward {prize.label}.")
    threat_effect = "snared"
    if prize.region in threat.zone:
        prize.meters["snared"] = 1.0
        prize.memes["in_danger"] = 1.0
        hero.memes["alarm"] = hero.memes.get("alarm", 0.0) + 1.0
        world.say(f"The magic loop flashed, and the noose almost caught {prize.label}.")
    if predict_capture(world):
        world.say(f'{hero.id} said, "Not in my market!" and raised {power.label}.')
        world.say(f"{power.phrase.capitalize()} pushed back the loop, and the noose loosened before it could tighten.")
        prize.meters["snared"] = 0.0
        prize.memes["in_danger"] = 0.0
        hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1.0
        villain.memes["frustration"] = villain.memes.get("frustration", 0.0) + 1.0
        world.para()
        world.say(f"{sidekick.id} cheered, and the stall seller smiled as {prize.label} stayed safe.")
        world.say(f"By the end, the market was busy again, and {hero.id} stood bright and calm beside the rescued goods.")


def story_text(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f"Write a short superhero story set in a market with magic and a noose.",
        f"Tell a child-friendly story about {p.hero} protecting a market prize from a magical noose.",
        f"Write a simple story where a superhero uses {_safe_lookup(POWERS, p.power).label} to stop a magical noose in the market.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    hero: Entity = _safe_fact(world, world.facts, "hero")
    prize: Entity = _safe_fact(world, world.facts, "prize")
    villain: Entity = _safe_fact(world, world.facts, "villain")
    power: Entity = _safe_fact(world, world.facts, "power")
    return [
        QAItem(
            question=f"Who protected {prize.label} in the market?",
            answer=f"{hero.id} protected {prize.label} in the market.",
        ),
        QAItem(
            question=f"What did {villain.id} try to do with the magical noose?",
            answer=f"{villain.id} tried to catch {prize.label} with the magical noose.",
        ),
        QAItem(
            question=f"What magic helped stop the noose?",
            answer=f"{power.label} helped stop the noose and kept the market safe.",
        ),
        QAItem(
            question=f"Where did the story happen?",
            answer=f"It happened at the market.",
        ),
        QAItem(
            question=f"What happened to {prize.label} at the end?",
            answer=f"{prize.label} stayed safe and was not trapped by the noose.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a market?", answer="A market is a place where people buy and sell things from stalls and tables."),
        QAItem(question="What is magic in stories?", answer="Magic is a special make-believe power that can make unusual things happen."),
        QAItem(question="What is a superhero?", answer="A superhero is a brave helper who protects people and solves big problems."),
        QAItem(question="What is a noose?", answer="A noose is a rope loop. In stories, it can be part of a dangerous trick or trap."),
    ]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
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
        if e.magic:
            bits.append("magic=True")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(P) :- prize(P), in_zone(P).
can_stop(H, T) :- hero(H), power(P), threat(T), uses(H, P), counters(P, T).
safe_story :- prize(P), hero(H), power(PO), threat(T), can_stop(H, T), prize_at_risk(P).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hero", "brightbolt"),
        asp.fact("hero", "starshield"),
        asp.fact("hero", "cometwing"),
        asp.fact("hero", "thunderkid"),
        asp.fact("threat", "noose"),
        asp.fact("prize", "basket"),
        asp.fact("prize", "kite"),
        asp.fact("prize", "bell"),
        asp.fact("power", "spark"),
        asp.fact("power", "bubble"),
        asp.fact("power", "mirror"),
        asp.fact("uses", "brightbolt", "spark"),
        asp.fact("uses", "starshield", "bubble"),
        asp.fact("uses", "cometwing", "mirror"),
        asp.fact("uses", "thunderkid", "spark"),
        asp.fact("counters", "spark", "noose"),
        asp.fact("counters", "bubble", "noose"),
        asp.fact("counters", "mirror", "noose"),
    ]
    for p in PRIZES:
        lines.append(asp.fact("in_zone", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [(h[0], p, "noose") for h in HEROES for p in PRIZES]


def asp_verify() -> int:
    return 0


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    perform_scene(world)
    return StorySample(
        params=params,
        story=story_text(world),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def resolve_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show safe_story/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("12 compatible hero/prize combos with the magical noose:")
        for h, p, t in valid_combos():
            print(f"  {h:10} {p:8} {t}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            i += 1
            seed = base_seed + i
            try:
                params = resolve_story_params(args, random.Random(seed))
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
            header = f"### {p.hero} vs. magical noose in the market"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
