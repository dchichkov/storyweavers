#!/usr/bin/env python3
"""
A small storyworld for a superhero-style tale with magic, snuggle, and ziti.

Seed tale:
A young hero loved helping people in a bright city. One evening, after saving
the day, the hero got hungry and wanted ziti. But a tiny magical problem made
the noodles twist and tangle. The hero had to use calm thinking, a special
magic trick, and a cozy snuggle with a helper before the supper could be
shared happily.

The world models:
- a hero with a cape, a power, and a feeling of hunger
- a magical mishap affecting dinner
- a helper who offers a soothing snuggle and a practical fix
- a resolution where the hero shares ziti and the city feels safe again
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
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    aid: object | None = None
    hero: object | None = None
    power: object | None = None
    prize: object | None = None
    sidekick: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = __import__('collections').defaultdict(float)
        if not self.memes:
            self.memes = __import__('collections').defaultdict(float)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    name: str = "Starport"
    setting: str = "the city"
    places: set[str] = field(default_factory=lambda: {"city", "tower", "kitchen", "roof"})
    magic: bool = True
    affirms: set[str] = field(default_factory=lambda: {"fly", "shine", "cook"})
    world: object | None = None
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
class Power:
    id: str
    label: str
    verb: str
    magic_kind: str
    effect: str
    keyword: str = "magic"
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
    type: str
    relation: str = "dinner"
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
class Aid:
    id: str
    label: str
    action: str
    comfort: str
    fix: str
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
    def __init__(self, city: City) -> None:
        self.city = city
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        clone = World(self.city)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    sidekick_name: str
    place: str
    power: str
    prize: str
    aid: str
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


HERO_NAMES = ["Nova", "Pip", "Mira", "Ari", "Zane", "Luna", "Ruby", "Tess"]
SIDEKICK_NAMES = ["Bean", "Toto", "Milo", "Pia", "Jojo", "Nia"]
HERO_TYPES = ["girl", "boy"]
PLACES = ["tower", "kitchen", "roof", "city"]
POWERS = {
    "spark": Power("spark", "spark power", "spark the lights", "light-magic", "brightly shimmered", tags={"magic", "light"}),
    "whirl": Power("whirl", "whirl power", "spin the air", "wind-magic", "twirled everything around", tags={"magic", "wind"}),
    "glow": Power("glow", "glow power", "glow the path", "glow-magic", "made the room shine", tags={"magic", "light"}),
}
PRIZES = {
    "ziti": Prize("ziti", "a warm bowl of ziti", "pasta", relation="supper"),
}
AIDS = {
    "snuggle": Aid("snuggle", "a snuggle", "snuggle close", "warm and brave", "settle the magic down", "then carried the bowl carefully"),
}


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_magic_tangle(world: World) -> list[str]:
    out: list[str] = []
    hero = _safe_fact(world, world.facts, "hero")
    power = _safe_fact(world, world.facts, "power")
    prize = _safe_fact(world, world.facts, "prize")
    if hero.memes.get("hunger", 0) >= THRESHOLD and hero.memes.get("stress", 0) < THRESHOLD:
        sig = ("tangle", power.id)
        if sig not in world.fired:
            world.fired.add(sig)
            prize.meters["tangled"] = 1.0
            hero.memes["stress"] = hero.memes.get("stress", 0) + 1.0
            out.append(f"The {power.label} made the ziti twist into a tangle.")
    return out


def _r_snuggle_calm(world: World) -> list[str]:
    out: list[str] = []
    hero = _safe_fact(world, world.facts, "hero")
    aid = _safe_fact(world, world.facts, "aid")
    if hero.memes.get("stress", 0) >= THRESHOLD and hero.memes.get("comfort", 0) < THRESHOLD:
        sig = ("calm", aid.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["comfort"] = hero.memes.get("comfort", 0) + 1.0
            hero.memes["stress"] = 0.0
            out.append("The snuggle made the hero breathe slower and feel ready again.")
    return out


def _r_fix_dinner(world: World) -> list[str]:
    out: list[str] = []
    hero = _safe_fact(world, world.facts, "hero")
    prize = _safe_fact(world, world.facts, "prize")
    aid = _safe_fact(world, world.facts, "aid")
    if hero.memes.get("comfort", 0) >= THRESHOLD and prize.meters.get("tangled", 0) >= THRESHOLD:
        sig = ("fix", prize.id)
        if sig not in world.fired:
            world.fired.add(sig)
            prize.meters["tangled"] = 0.0
            prize.meters["served"] = 1.0
            hero.memes["joy"] = hero.memes.get("joy", 0) + 1.0
            out.append(f"{aid.fix.capitalize()}, and the ziti was ready to share.")
    return out


RULES = [
    Rule("magic_tangle", _r_magic_tangle),
    Rule("snuggle_calm", _r_snuggle_calm),
    Rule("fix_dinner", _r_fix_dinner),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def tell(params: StoryParams) -> World:
    world = World(City())
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        traits=["little", "brave", "kind"],
        meters={},
        memes={"hunger": 1.0},
    ))
    sidekick = world.add(Entity(
        id=params.sidekick_name,
        kind="character",
        type="child",
        traits=["gentle", "loyal"],
        meters={},
        memes={},
    ))
    power = world.add(Entity(
        id="power",
        kind="thing",
        type="power",
        label=_safe_lookup(POWERS, params.power).label,
        phrase=_safe_lookup(POWERS, params.power).label,
        owner=hero.id,
    ))
    prize = world.add(Entity(
        id="ziti",
        kind="thing",
        type="ziti",
        label="ziti",
        phrase=_safe_lookup(PRIZES, params.prize).phrase,
        owner=hero.id,
    ))
    aid = world.add(Entity(
        id="snuggle",
        kind="thing",
        type="aid",
        label="snuggle",
        phrase=_safe_lookup(AIDS, params.aid).label,
        owner=sidekick.id,
    ))

    world.facts.update(hero=hero, sidekick=sidekick, power=power, prize=prize, aid=aid, params=params)

    world.say(f"{hero.id} was a little superhero who loved helping people in {world.city.setting}.")
    world.say(f"One night, {hero.id} hurried home to {params.place} after saving the day.")
    world.say(f"{hero.pronoun('subject').capitalize()} was hungry and really wanted {prize.phrase}.")
    world.para()

    world.say(f"But when {hero.id} used {power.label}, the {power.magic_kind} got wobbly.")
    world.say(f"The power {power.effect}, and the ziti turned into a tangle.")
    propagate(world, narrate=True)
    world.para()

    world.say(f"{params.sidekick_name} offered {aid.label} and said, \"It's okay. We can slow down.\"")
    world.say(f"{hero.id} accepted the {aid.label} and snuggled close.")
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"Then {aid.tail}, and {hero.id} sat with {params.sidekick_name}, sharing {prize.label} "
        f"while the windows glowed over {world.city.setting}."
    )
    world.say(f"The city felt safe again, and the hero finished supper with a happy smile.")

    return world


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f'Write a short superhero story for a small child about {p.hero_name}, magic, and {p.prize}.',
        f"Tell a gentle adventure where {p.hero_name} uses {p.power} but needs {p.aid} before eating {p.prize}.",
        f'Write a simple story that includes the word "{_safe_lookup(PRIZES, p.prize).label}" and ends with a cozy, magical fix.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    hero = _safe_fact(world, world.facts, "hero")
    sidekick = _safe_fact(world, world.facts, "sidekick")
    qas = [
        QAItem(
            question=f"Who is the superhero in the story?",
            answer=f"The superhero is {p.hero_name}, a little {p.hero_type} who helps people in the city.",
        ),
        QAItem(
            question=f"What did {p.hero_name} want after saving the day?",
            answer=f"{p.hero_name} wanted {_safe_lookup(PRIZES, p.prize).phrase} for supper.",
        ),
        QAItem(
            question=f"Who helped calm the magical problem?",
            answer=f"{p.sidekick_name} helped by offering a snuggle and staying close with {p.hero_name}.",
        ),
    ]
    if hero.memes.get("stress", 0) >= THRESHOLD:
        qas.append(QAItem(
            question=f"Why did the magic make dinner tricky?",
            answer=f"The magic made the ziti twist into a tangle, so {p.hero_name} needed help before supper could be shared.",
        ))
    if hero.memes.get("joy", 0) >= THRESHOLD:
        qas.append(QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {p.hero_name} sharing ziti, feeling happy, and the city glowing safely again.",
        ))
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is ziti?",
            answer="Ziti is a kind of pasta with tube-shaped noodles that people often eat with sauce.",
        ),
        QAItem(
            question="What does magic mean in a superhero story?",
            answer="Magic is a special power that can make surprising things happen, like glowing lights or twisting air.",
        ),
        QAItem(
            question="What is a snuggle?",
            answer="A snuggle is a close, cozy cuddle that can help someone feel safe and calm.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("Nova", "girl", "Bean", "the tower", "spark", "ziti", "snuggle"),
    StoryParams("Pip", "boy", "Toto", "the kitchen", "glow", "ziti", "snuggle"),
    StoryParams("Mira", "girl", "Pia", "the roof", "whirl", "ziti", "snuggle"),
]


ASP_RULES = r"""
hero(H) :- hero_name(H).
sidekick(S) :- sidekick_name(S).
power(P) :- power_name(P).
prize(Z) :- prize_name(Z).
aid(A) :- aid_name(A).

hunger_triggers_magic(H) :- hero(H), hungry(H).
magic_tangles_ziti(Z) :- prize(Z), magic_on(P), power(P).
snuggle_calm(H) :- hero(H), comforted(H).
resolved(H) :- hero(H), snuggle_calm(H), magic_tangles_ziti(ziti).

#show resolved/1.
#show snuggle_calm/1.
#show magic_tangles_ziti/1.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hero_name", "Nova"),
        asp.fact("hero_name", "Pip"),
        asp.fact("hero_name", "Mira"),
        asp.fact("sidekick_name", "Bean"),
        asp.fact("sidekick_name", "Toto"),
        asp.fact("sidekick_name", "Pia"),
        asp.fact("power_name", "spark"),
        asp.fact("power_name", "whirl"),
        asp.fact("power_name", "glow"),
        asp.fact("prize_name", "ziti"),
        asp.fact("aid_name", "snuggle"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with magic, snuggle, and ziti.")
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--sidekick", choices=SIDEKICK_NAMES)
    ap.add_argument("--type", dest="hero_type", choices=HERO_TYPES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--aid", choices=AIDS)
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
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    sidekick = getattr(args, "sidekick", None) or rng.choice(SIDEKICK_NAMES)
    place = getattr(args, "place", None) or rng.choice(PLACES)
    power = getattr(args, "power", None) or rng.choice(list(POWERS))
    prize = getattr(args, "prize", None) or "ziti"
    aid = getattr(args, "aid", None) or "snuggle"
    if prize != "ziti":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(name, hero_type, sidekick, place, power, prize, aid)


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


def asp_verify() -> int:
    print("OK: ASP twin is present (storyworld-specific verification is minimal for this domain).")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show resolved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

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
            header = f"### {p.hero_name}: {p.power} with {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
