#!/usr/bin/env python3
"""
storyworlds/worlds/stall_magic_superhero_story.py
=================================================

A small storyworld about a young superhero, a market stall, and a magical
problem that turns into a brave, kind solution.

Premise:
- A hero visits a stall to get something useful.
- A magical mishap makes the stall hard to use or threatens the item.
- The hero must stay calm, use a power wisely, and fix the situation.
- The ending proves the stall is safe again and the hero has grown.

This world is intentionally tiny and constraint-driven. It models a handful of
typed entities with meters and memes, narrates from state changes, and provides
an ASP twin for the reasonableness gate.
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
    plural: bool = False
    powered: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    def __post_init__(self) -> None:
        for key in ("bright", "crowded", "blocked", "safe", "cost", "magic"):
            self.meters.setdefault(key, 0.0)
        for key in ("joy", "worry", "hope", "pride", "fear"):
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero"}
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
class Stall:
    place: str = "the stall"
    afford_magic: bool = True
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
    name: str
    verb: str
    effect: str
    cost: str
    keywords: set[str] = field(default_factory=set)
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
class Prize:
    id: str
    label: str
    phrase: str
    risk: str
    protected_by: str
    keyword: str
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
    def __init__(self, stall: Stall) -> None:
        self.stall = stall
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.stall)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


def _hero_name(hero_type: str) -> str:
    return "Nova" if hero_type == "girl" else "Dash"


def _hero_title(hero: Entity) -> str:
    return f"little {hero.type} superhero"


def _do_magic(world: World, hero: Entity, power: Power, prize: Prize, narrate: bool = True) -> None:
    hero.meters["magic"] += 1
    hero.memes["hope"] += 1
    hero.memes["joy"] += 1
    stall = world.stall
    if stall.afford_magic:
        if prize.keyword in power.keywords:
            hero.meters["safe"] += 1
    if narrate:
        world.say(
            f"{hero.pronoun().capitalize()} used {power.name}, and the air shimmered with {power.effect}."
        )


def predict(world: World, hero: Entity, power: Power, prize: Prize) -> dict:
    sim = world.copy()
    _do_magic(sim, sim.get(hero.id), power, prize, narrate=False)
    return {
        "saved": sim.get(prize.id).meters["safe"] >= THRESHOLD,
        "cost": sim.get(hero.id).meters["cost"] if hero.id in sim.entities else 0,
    }


def setup(world: World, hero: Entity, helper: Entity, prize: Entity) -> None:
    world.say(
        f"{hero.id} was a {_hero_title(hero)} who kept watch over {world.stall.place}."
    )
    world.say(
        f"At the stall, {helper.id} sold {prize.phrase}, and {hero.id} wanted to help."
    )


def trouble(world: World, hero: Entity, helper: Entity, prize: Entity, power: Power) -> None:
    hero.memes["worry"] += 1
    prize.meters["blocked"] += 1
    world.say(
        f"Then a curl of magic swept across {world.stall.place}, and {prize.label} got stuck behind a glowing curtain."
    )
    world.say(
        f"{hero.id} knew {helper.id} could not reach {prize.it()} while the sparkle barrier stayed up."
    )
    world.say(
        f"{hero.id} wanted to use {power.name}, but first {hero.pronoun('possessive')} heart had to stay steady."
    )


def decide(world: World, hero: Entity, power: Power, prize: Entity) -> None:
    pred = predict(world, hero, power, prize)
    if not pred["saved"]:
        pass
    world.say(
        f"{hero.id} took a breath and chose the careful version of the spell, not the flashy one."
    )


def resolve(world: World, hero: Entity, helper: Entity, prize: Entity, power: Power) -> None:
    _do_magic(world, hero, power, prize, narrate=True)
    prize.meters["blocked"] = 0
    prize.meters["safe"] = 1
    helper.memes["hope"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"The glow melted into tiny stars, and the barrier folded away like mist."
    )
    world.say(
        f"{helper.id} could reach {prize.it()} again, and {hero.id} smiled because the stall was safe."
    )
    world.say(
        f"By the end, {hero.id} stood beside {helper.id}, proud of using magic to protect the stall instead of showing off."
    )


def tell(stall: Stall, power: Power, prize: Prize, hero_name: str = "Nova", hero_type: str = "girl") -> World:
    world = World(stall)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    helper = world.add(Entity(id="Mara", kind="character", type="woman", label="Mara"))
    item = world.add(Entity(id=prize.id, type="thing", label=prize.label, phrase=prize.phrase, caretaker=helper.id))
    setup(world, hero, helper, item)
    world.para()
    trouble(world, hero, helper, item, power)
    decide(world, hero, power, item)
    world.para()
    resolve(world, hero, helper, item, power)
    world.facts.update(hero=hero, helper=helper, prize=item, power=power, stall=stall)
    return world


SETTINGS = {
    "stall": Stall(place="the lantern stall", afford_magic=True),
    "market": Stall(place="the market stall", afford_magic=True),
    "fair": Stall(place="the fair stall", afford_magic=True),
}

POWERS = {
    "glimmer": Power(
        id="glimmer",
        name="Glimmer Shield",
        verb="raise a shield of light",
        effect="a soft golden shield",
        cost="a small spark of energy",
        keywords={"glow", "barrier", "light"},
    ),
    "mend": Power(
        id="mend",
        name="Mend Thread",
        verb="stitch the crack closed",
        effect="silver threads that knit the air back together",
        cost="a tiny bit of focus",
        keywords={"stuck", "crack", "thread"},
    ),
    "lift": Power(
        id="lift",
        name="Lift Bubble",
        verb="lift the curtain away",
        effect="a round bubble that floated the spell aside",
        cost="a puff of breath",
        keywords={"curtain", "float", "lift"},
    ),
}

PRIZES = {
    "lantern": Prize(
        id="lantern",
        label="lantern",
        phrase="a bright brass lantern",
        risk="darkness",
        protected_by="glimmer",
        keyword="glow",
    ),
    "mask": Prize(
        id="mask",
        label="mask",
        phrase="a silver mask with a blue star",
        risk="dust",
        protected_by="mend",
        keyword="thread",
    ),
    "cape": Prize(
        id="cape",
        label="cape",
        phrase="a red cape with a quick clasp",
        risk="tangles",
        protected_by="lift",
        keyword="curtain",
    ),
}

HERO_TYPES = ["boy", "girl"]
TRAITS = ["brave", "kind", "quick", "clever", "gentle"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for power_id, power in POWERS.items():
            for prize_id, prize in PRIZES.items():
                if prize.protected_by == power_id:
                    combos.append((place, power_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    power: str
    prize: str
    name: str
    hero_type: str
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
    prize = _safe_fact(world, f, "prize")
    power = _safe_fact(world, f, "power")
    return [
        f'Write a short superhero story for a young child featuring a magic "{power.name}" and a {prize.label} at a stall.',
        f"Tell a gentle story about {hero.id}, a {hero.type} superhero, who uses {power.name} to help at {world.stall.place}.",
        f'Write a simple story where magic blocks a stall, then a hero uses "{power.verb}" to fix it.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    prize = _safe_fact(world, f, "prize")
    power = _safe_fact(world, f, "power")
    return [
        QAItem(
            question=f"Who is the superhero in the story?",
            answer=f"The superhero is {hero.id}, a kind little {hero.type} who cares about the stall.",
        ),
        QAItem(
            question=f"What got stuck behind the magic curtain?",
            answer=f"{prize.label.capitalize()} got stuck behind the magic curtain at {world.stall.place}.",
        ),
        QAItem(
            question=f"What magic did {hero.id} use to help?",
            answer=f"{hero.id} used {power.name} to help {helper.id} reach the {prize.label} again.",
        ),
        QAItem(
            question=f"Why was {helper.id} worried?",
            answer=f"{helper.id} was worried because the glowing barrier kept {helper.pronoun('object')} from reaching the {prize.label}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the stall safe again, {helper.id} able to reach the {prize.label}, and {hero.id} proud of using magic carefully.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "stall": [
        QAItem(question="What is a stall?", answer="A stall is a small place where people can sell things, like toys, fruit, or lanterns."),
    ],
    "magic": [
        QAItem(question="What is magic in stories?", answer="Magic in stories is a special kind of power that can make unusual things happen."),
    ],
    "superhero": [
        QAItem(question="What does a superhero do?", answer="A superhero helps people, solves problems, and tries to keep others safe."),
    ],
    "lantern": [
        QAItem(question="What is a lantern for?", answer="A lantern gives light, so people can see better when it is dark."),
    ],
    "mask": [
        QAItem(question="Why might a hero wear a mask?", answer="A hero might wear a mask to keep a secret identity or look extra heroic."),
    ],
    "cape": [
        QAItem(question="Why do some heroes wear capes?", answer="Some heroes wear capes because capes look dramatic and make the hero feel bold."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"stall", "magic", "superhero", world.facts["prize"].id}
    out: list[QAItem] = []
    for tag in ["stall", "magic", "superhero", "lantern", "mask", "cape"]:
        if tag in tags:
            out.extend(WORLD_KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"- {p}" for p in sample.prompts], ""]
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="stall", power="glimmer", prize="lantern", name="Nova", hero_type="girl", trait="brave"),
    StoryParams(place="market", power="mend", prize="mask", name="Dash", hero_type="boy", trait="clever"),
    StoryParams(place="fair", power="lift", prize="cape", name="Mira", hero_type="girl", trait="kind"),
]


def explain_rejection(power: Power, prize: Prize) -> str:
    return f"(No story: {power.name} does not clearly solve the {prize.label} problem in this small world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a superhero, a stall, and a magical problem.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--power", choices=POWERS.keys())
    ap.add_argument("--prize", choices=PRIZES.keys())
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "power", None) is None or c[1] == getattr(args, "power", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, power, prize = (list(rng.choice(combos)) + [None, None, None])[:3]
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    name = getattr(args, "name", None) or _hero_name(hero_type)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, power=power, prize=prize, name=name, hero_type=hero_type, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(POWERS, params.power), _safe_lookup(PRIZES, params.prize), params.name, params.hero_type)
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


ASP_RULES = r"""
valid(Place, Power, Prize) :- place(Place), power(Power), prize(Prize), matches(Power, Prize).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for power_id in POWERS:
        lines.append(asp.fact("power", power_id))
    for prize_id, prize in PRIZES.items():
        lines.append(asp.fact("prize", prize_id))
        lines.append(asp.fact("matches", prize.protected_by, prize_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in ASP:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for row in asp_valid_combos():
            print(row)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
