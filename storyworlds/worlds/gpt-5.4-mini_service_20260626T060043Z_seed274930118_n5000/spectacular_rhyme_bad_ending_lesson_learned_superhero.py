#!/usr/bin/env python3
"""
A small superhero storyworld with rhyme, a bad ending, and a lesson learned.

Premise:
- A young superhero loves a spectacular helper tool.
- A villain causes trouble in the city.
- The hero tries to stop it, but a flashy choice makes things worse.
- The hero learns that teamwork and careful planning matter more than showing off.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
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
    helper: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    power: object | None = None
    sidekick: object | None = None
    villain: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "heroine"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "hero"}:
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
    name: str
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
class Power:
    id: str
    label: str
    verb: str
    rhyme: str
    risk: str
    mess: str
    counter: str
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
class Villain:
    id: str
    label: str
    trouble: str
    rhyme: str
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.ending_bad = False

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.ending_bad = self.ending_bad
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    setting: str
    power: str
    villain: str
    hero_name: str
    hero_type: str
    sidekick_name: str
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


SETTINGS = {
    "city": Setting(place="the city", name="the city", affords={"flight", "shield"}),
    "harbor": Setting(place="the harbor", name="the harbor", affords={"flight"}),
    "museum": Setting(place="the museum", name="the museum", affords={"shield"}),
}

POWERS = {
    "flight": Power(
        id="flight",
        label="wind boots",
        verb="zoom through the sky",
        rhyme="high",
        risk="overfly",
        mess="scatter",
        counter="listen to the team and slow down",
    ),
    "shield": Power(
        id="shield",
        label="star shield",
        verb="block the blast",
        rhyme="bright",
        risk="charge ahead",
        mess="crash",
        counter="ask for help and hold steady",
    ),
}

VILLAINS = {
    "glimmer": Villain(
        id="glimmer",
        label="Glimmer Greed",
        trouble="stole the city bells",
        rhyme="gleam",
    ),
    "whirl": Villain(
        id="whirl",
        label="Whirlwind Wobble",
        trouble="sent papers swirling",
        rhyme="twirl",
    ),
}

HERO_NAMES = ["Nova", "Ruby", "Pip", "Skye", "Milo", "Ivy"]
SIDEKICKS = ["Toby", "Luna", "Jules", "Mina", "Rae"]


def rhyme_line(hero: Entity, power: Power, villain: Villain) -> str:
    return (
        f"{hero.id} would leap with a grin and a gleam, "
        f"to chase {villain.label} like a bright little dream; "
        f"but rushing too fast can go wrong in a blink, "
        f"so brave hearts must pause and remember to think."
    )


def setup_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, label="hero"))
    sidekick = world.add(Entity(id=params.sidekick_name, kind="character", type="child", label="sidekick"))
    villain = world.add(Entity(id="villain", kind="character", type="villain", label=_safe_lookup(VILLAINS, params.villain).label))
    power = world.add(Entity(id="power", kind="thing", type="gear", label=_safe_lookup(POWERS, params.power).label))
    hero.worn_by = hero.id
    power.owner = hero.id
    world.facts.update(hero=hero, sidekick=sidekick, villain=villain, power=power, params=params)
    return world


def predict_mess(world: World, power: Power) -> bool:
    sim = world.copy()
    sim.get("hero").meters[power.mess] = 1.0
    return True


def tell(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    sidekick: Entity = _safe_fact(world, world.facts, "sidekick")
    villain_def = VILLAINS[world.facts["params"].villain]
    power_def = POWERS[world.facts["params"].power]

    hero.memes["hope"] = 1
    world.say(
        f"On a spectacular day in {world.setting.name}, {hero.id} wore {power_def.label} "
        f"and felt ready to help."
    )
    world.say(
        f"{hero.id} and {sidekick.id} heard that {villain_def.label} had {villain_def.trouble}."
    )
    world.say(rhyme_line(hero, power_def, villain_def))

    world.para()
    hero.memes["pride"] = 1
    world.say(
        f"{hero.id} said, \"I can fix it all by myself!\" and rushed to "
        f"{power_def.verb} before anyone could warn {hero.pronoun('object')}."
    )
    hero.meters[power_def.mess] = 1.0
    world.say(
        f"The hurry made a mess instead: the sky shook, the ropes snapped, and "
        f"{villain_def.label} slipped away with a sneaky grin."
    )

    world.para()
    world.ending_bad = True
    hero.memes["sad"] = 1
    sidekick.memes["worry"] = 1
    world.say(
        f"{hero.id} landed in a frown. {sidekick.id} pointed to the broken plan and said, "
        f"\"A big job needs two brave heads, not one flashy hop.\""
    )
    world.say(
        f"{hero.id} took a slow breath and learned the lesson at last: to save the day, "
        f"{hero.pronoun()} should {power_def.counter}."
    )
    world.say(
        f"So the story ended a little badly, but wisely: {hero.id} stopped showing off, "
        f"and the next time the city needed help, {hero.id} would ask {sidekick.id} first."
    )

    world.facts["lesson"] = f"{hero.id} learned to {power_def.counter}."
    world.facts["bad_ending"] = True


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    power = _safe_lookup(POWERS, p.power)
    villain = _safe_lookup(VILLAINS, p.villain)
    return [
        f'Write a spectacular superhero story in rhyme about {p.hero_name} and {villain.label}.',
        f"Tell a child-friendly superhero tale where {p.hero_name} tries to use {power.label} alone and learns a lesson.",
        "Make the ending bad, but the lesson useful and kind.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    hero: Entity = _safe_fact(world, world.facts, "hero")
    sidekick: Entity = _safe_fact(world, world.facts, "sidekick")
    villain_def = _safe_lookup(VILLAINS, p.villain)
    power_def = _safe_lookup(POWERS, p.power)
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a young superhero, and {sidekick.id}, who helped in the city.",
        ),
        QAItem(
            question=f"What did {hero.id} try to do first?",
            answer=f"{hero.id} tried to {power_def.verb} alone and stop {villain_def.label} quickly.",
        ),
        QAItem(
            question=f"Why did the plan go wrong?",
            answer=f"The plan went wrong because {hero.id} rushed ahead, made a mess, and let {villain_def.label} escape.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned to {power_def.counter}, because teamwork works better than showing off.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a brave character who uses special powers to help people and solve problems.",
        ),
        QAItem(
            question="Why is teamwork helpful?",
            answer="Teamwork is helpful because two or more people can share ideas, notice danger, and finish a hard job together.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is a good idea a character understands after something goes wrong.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes}")
    lines.append(f"ending_bad={world.ending_bad}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(h1).
sidekick(s1).
villain(v1).
power(p1).

bad_ending :- rush(h1), mess(p1), escape(v1).
lesson_learned :- bad_ending, teamwork_needed.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("hero", "h1"),
            asp.fact("sidekick", "s1"),
            asp.fact("villain", "v1"),
            asp.fact("power", "p1"),
            asp.fact("rush", "h1"),
            asp.fact("mess", "p1"),
            asp.fact("escape", "v1"),
            asp.fact("teamwork_needed"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Spectacular superhero storyworld with rhyme, bad ending, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--villain", choices=VILLAINS)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
    ap.add_argument("--gender", choices=["boy", "girl"])
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    power = getattr(args, "power", None) or rng.choice(list(POWERS))
    villain = getattr(args, "villain", None) or rng.choice(list(VILLAINS))
    if power not in _safe_lookup(SETTINGS, setting).affords:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["boy", "girl"])
    if getattr(args, "name", None):
        hero_name = getattr(args, "name", None)
    else:
        hero_name = rng.choice(HERO_NAMES)
    sidekick = getattr(args, "sidekick", None) or rng.choice([n for n in SIDEKICKS if n != hero_name])
    return StoryParams(setting=setting, power=power, villain=villain, hero_name=hero_name, hero_type=gender, sidekick_name=sidekick)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell(world)
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


def valid_story_combos() -> list[tuple[str, str, str]]:
    out = []
    for s, setting in SETTINGS.items():
        for p in setting.affords:
            for v in VILLAINS:
                out.append((s, p, v))
    return out


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_story_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(setting="city", power="flight", villain="glimmer", hero_name="Nova", hero_type="girl", sidekick_name="Toby"),
    StoryParams(setting="museum", power="shield", villain="whirl", hero_name="Pip", hero_type="boy", sidekick_name="Luna"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print("\n".join(map(str, vals)))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
