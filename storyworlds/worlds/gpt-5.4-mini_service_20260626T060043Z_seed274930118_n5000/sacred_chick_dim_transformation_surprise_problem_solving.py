#!/usr/bin/env python3
"""
A standalone storyworld for a tiny superhero tale with sacred, chick-dim
transformation, surprise, and problem solving.

Premise:
- A small hero loves helping in a bright city.
- A sacred charm can trigger a chick-dim transformation.
- A surprise problem appears, and the hero must solve it without breaking
  the charm's rules.

The world is intentionally small and constraint-checked so every generated
story has a clear setup, a turn, and a resolution.
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    charm: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    affords: set[str] = field(default_factory=set)
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
    phrase: str
    trigger: str
    effect: str
    transform_to: str
    transformation_name: str
    surprise: str
    problem: str
    solution: str
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
class Problem:
    id: str
    label: str
    phrase: str
    risk: str
    solved_by: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        import copy as _copy
        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


def _set_meter(ent: Entity, key: str, value: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + value


def _set_meme(ent: Entity, key: str, value: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + value


def hero_intro(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a small {hero.type} superhero who protected {world.setting.place} "
        f"with a brave heart."
    )


def sacred_intro(world: World, hero: Entity, charm: Entity, power: Power) -> None:
    world.say(
        f"{hero.id} kept {hero.pronoun('possessive')} {charm.label} close because it was sacred "
        f"and full of {power.label}."
    )
    world.say(
        f"When {hero.id} held it and whispered the old words, {power.transformation_name} began."
    )


def transform(world: World, hero: Entity, power: Power) -> None:
    if hero.memes.get("transformed", 0.0) >= THRESHOLD:
        return
    _set_meme(hero, "transformed", 1)
    _set_meter(hero, "size_change", 1)
    _set_meter(hero, "power", 1)
    hero.type = power.transform_to
    world.say(
        f"In a bright flash, {hero.id} changed into a {power.transform_to} form, {power.effect}."
    )


def surprise(problem: Problem, hero: Entity) -> str:
    return (
        f"Suddenly, {problem.surprise} appeared, and the city needed help right away."
    )


def solve_problem(world: World, hero: Entity, problem: Problem, power: Power) -> None:
    _set_meme(hero, "problem_solving", 1)
    _set_meter(hero, "help", 1)
    world.say(
        f"{hero.id} did not panic. {hero.pronoun().capitalize()} looked at the problem and used "
        f"{power.solution}."
    )
    world.say(
        f"That {problem.solution} fixed the danger, and {hero.id} saved the day."
    )


def resolve_story(world: World, hero: Entity, charm: Entity, power: Power, problem: Problem) -> None:
    _set_meme(hero, "joy", 1)
    world.say(
        f"At the end, {hero.id} tucked the sacred {charm.label} away and smiled at the calm sky."
    )
    world.say(
        f"The little {hero.type} superhero stayed transformed just long enough to help, "
        f"then the day felt safe again."
    )


SETTINGS = {
    "city_square": Setting(place="the city square", affords={"transformation", "problem_solving"}),
    "rooftops": Setting(place="the rooftops", affords={"transformation", "problem_solving"}),
    "museum": Setting(place="the museum hall", affords={"transformation", "problem_solving"}),
}

POWERS = {
    "chick_dim": Power(
        id="chick_dim",
        label="chick-dim glow",
        phrase="a sacred chick-dim shimmer",
        trigger="a gentle squeeze",
        effect="tiny feathers of light danced around the hero",
        transform_to="chick-dim hero",
        transformation_name="the chick-dim transformation",
        surprise="a runaway drone",
        problem="the drone blocked the museum dome",
        solution="a quick feather-flash dive and a redirecting flap",
        tags={"sacred", "chick-dim", "transformation", "surprise", "problem_solving"},
    ),
    "sunburst": Power(
        id="sunburst",
        label="sunburst spark",
        phrase="a sacred sunburst shimmer",
        trigger="a brave tap",
        effect="gold light rolled over the hero's cape",
        transform_to="sunburst hero",
        transformation_name="the sunburst transformation",
        surprise="a cracked traffic light",
        problem="the crossing had turned unsafe",
        solution="a fast shield pose and a glowing warning beam",
        tags={"sacred", "transformation", "surprise", "problem_solving"},
    ),
}

PROBLEMS = {
    "drone": Problem(
        id="drone",
        label="drone",
        phrase="a runaway drone",
        risk="it could crash into the glass dome",
        solved_by="feather-flash",
        tags={"surprise", "problem_solving"},
    ),
    "floodgate": Problem(
        id="floodgate",
        label="floodgate",
        phrase="a jammed floodgate",
        risk="water could spill into the street",
        solved_by="beam",
        tags={"surprise", "problem_solving"},
    ),
}

HERO_NAMES = ["Mina", "Rae", "Tess", "Nia", "Lio", "Kai"]
HERO_TYPES = ["girl", "boy"]
TRAITS = ["brave", "gentle", "clever", "quick", "kind"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for power_id in POWERS:
            for problem_id in PROBLEMS:
                if "transformation" in setting.affords and "problem_solving" in setting.affords:
                    combos.append((place, power_id, problem_id))
    return combos


@dataclass
class StoryParams:
    place: str
    power: str
    problem: str
    name: str
    gender: str
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
    ap = argparse.ArgumentParser(description="Superhero storyworld with sacred chick-dim transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--gender", choices=HERO_TYPES)
    ap.add_argument("--name")
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
              and (getattr(args, "problem", None) is None or c[2] == getattr(args, "problem", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, power, problem = (list(rng.choice(combos)) + [None, None, None])[:3]
    gender = getattr(args, "gender", None) or rng.choice(HERO_TYPES)
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, power=power, problem=problem, name=name, gender=gender, trait=trait)


def tell(setting: Setting, power: Power, problem: Problem, name: str, gender: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, traits=[trait, "heroic"]))
    charm = world.add(Entity(id="charm", type="charm", label="sacred charm", owner=hero.id))
    hero.meters["ready"] = 1
    hero.memes["care"] = 1

    hero_intro(world, hero)
    world.para()
    sacred_intro(world, hero, charm, power)
    transform(world, hero, power)
    world.para()
    world.say(surprise(problem, hero))
    world.say(
        f"The surprise was not just noisy; {problem.risk}."
    )
    solve_problem(world, hero, problem, power)
    world.para()
    resolve_story(world, hero, charm, power, problem)

    world.facts.update(hero=hero, charm=charm, power=power, problem=problem, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, power, problem = f["hero"], f["power"], f["problem"]
    return [
        f"Write a short superhero story for a child about {hero.id}, a sacred charm, and a {power.id} transformation.",
        f"Tell a story where {hero.id} gets a surprise problem and solves it after using {power.label}.",
        f"Create a gentle superhero tale that includes the words sacred, chick-dim, surprise, transformation, and problem solving.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, power, problem = f["hero"], f["power"], f["problem"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a small superhero who uses {power.label} to help.",
        ),
        QAItem(
            question=f"What caused the transformation?",
            answer=f"The sacred {power.label} and the old whispered words caused the chick-dim transformation.",
        ),
        QAItem(
            question=f"What surprise problem showed up?",
            answer=f"{problem.phrase} showed up, and it could cause trouble in the city.",
        ),
        QAItem(
            question=f"How was the problem solved?",
            answer=f"{hero.id} used {power.solution} to solve the problem quickly and safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a character who uses special powers or brave actions to help others.",
        ),
        QAItem(
            question="What does sacred mean?",
            answer="Sacred means something is very special, respected, and treated with care.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is when something changes into a new form.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means looking at a difficulty and finding a way to fix it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for pid, p in POWERS.items():
        lines.append(asp.fact("power", pid))
        lines.append(asp.fact("transforms_to", pid, p.transform_to))
        for t in sorted(p.tags):
            lines.append(asp.fact("tagged", pid, t))
    for pid, pr in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for t in sorted(pr.tags):
            lines.append(asp.fact("tagged_problem", pid, t))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Power, Problem) :- setting(Place), power(Power), problem(Problem),
                                affords(Place, transformation), affords(Place, problem_solving).

show_story(Place, Power, Problem) :- valid(Place, Power, Problem).
"""


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
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH")
    if py - cl:
        print("only python:", sorted(py - cl))
    if cl - py:
        print("only asp:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(POWERS, params.power), _safe_lookup(PROBLEMS, params.problem),
                 params.name, params.gender, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(place="city_square", power="chick_dim", problem="drone", name="Mina", gender="girl", trait="clever"),
    StoryParams(place="rooftops", power="chick_dim", problem="floodgate", name="Rae", gender="boy", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} valid combos:")
        for t in triples:
            print(t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
