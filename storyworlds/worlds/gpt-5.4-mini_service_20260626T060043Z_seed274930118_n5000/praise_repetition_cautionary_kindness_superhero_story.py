#!/usr/bin/env python3
"""
A standalone story world for a small Superhero Story about praise, repetition,
caution, and kindness.

The seed premise:
A young superhero wants to help people right away, but must learn that being
kind also means being careful and repeating a safe plan until everyone feels
ready. Praise helps the hero stay brave.
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

HERO_NAMES = ["Nova", "Pip", "Zuri", "Milo", "Juno", "Iris", "Arlo", "Tessa"]
HELPER_NAMES = ["Captain Bright", "Aunt Beacon", "Coach Star", "Ms. Halo"]
CITY_NAMES = ["Sunrise City", "Rivergate", "Bluebell Town", "Clover City"]
MISHAPS = ["a stuck kite", "a blocked bridge", "a fallen sign", "a lost kitten", "a jammed door"]
TOOLS = ["a rope", "a flashlight", "a ladder", "a map", "a walkie-talkie"]
ACTIONS = ["climb", "carry", "lift", "guide", "reach", "steady"]
TRAITS = ["brave", "eager", "gentle", "careful", "friendly", "cheerful"]



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

@dataclass
class Hero:
    name: str
    title: str
    trait: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    hero: object | None = None
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
class Helper:
    name: str
    role: str
    helper: object | None = None
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
class Problem:
    thing: str
    place: str
    risk: str
    caution_rule: str
    repetition_line: str
    problem: object | None = None
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
class World:
    hero: Hero
    helper: Helper
    problem: Problem
    tool: str
    city: str
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.facts.setdefault("story_lines", []).append(text)

    def render(self) -> str:
        return " ".join(self.facts.get("story_lines", []))
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
class StoryParams:
    hero: str
    helper: str
    city: str
    mishap: str
    tool: str
    trait: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero Story world with praise, repetition, caution, and kindness.")
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--city", choices=CITY_NAMES)
    ap.add_argument("--mishap", choices=MISHAPS)
    ap.add_argument("--tool", choices=TOOLS)
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


def valid_combo(params: StoryParams) -> bool:
    return params.tool in {"a rope", "a flashlight", "a ladder", "a map", "a walkie-talkie"}


def asp_facts() -> str:
    import asp
    lines = []
    for h in HERO_NAMES:
        lines.append(asp.fact("hero", h))
    for h in HELPER_NAMES:
        lines.append(asp.fact("helper", h))
    for c in CITY_NAMES:
        lines.append(asp.fact("city", c))
    for m in MISHAPS:
        lines.append(asp.fact("mishap", m))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    return "\n".join(lines)


ASP_RULES = r"""
selected(H,He,C,M,T) :- hero(H), helper(He), city(C), mishap(M), tool(T).
good(T) :- tool(T).
valid(H,He,C,M,T) :- selected(H,He,C,M,T), good(T).
#show valid/5.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set()
    for h in HERO_NAMES:
        for he in HELPER_NAMES:
            for c in CITY_NAMES:
                for m in MISHAPS:
                    for t in TOOLS:
                        if valid_combo(StoryParams(h, he, c, m, t, "brave")):
                            py.add((h, he, c, m, t))
    cl = set(asp_valid())
    if cl == py:
        print(f"OK: clingo gate matches Python ({len(cl)} combos).")
        return 0
    print("MISMATCH:")
    print("only in clingo:", sorted(cl - py))
    print("only in python:", sorted(py - cl))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = getattr(args, "hero", None) or rng.choice(HERO_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    city = getattr(args, "city", None) or rng.choice(CITY_NAMES)
    mishap = getattr(args, "mishap", None) or rng.choice(MISHAPS)
    tool = getattr(args, "tool", None) or rng.choice(TOOLS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    params = StoryParams(hero=hero, helper=helper, city=city, mishap=mishap, tool=tool, trait=trait)
    if not valid_combo(params):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return params


def make_world(params: StoryParams) -> World:
    hero = Hero(
        name=params.hero,
        title="superhero",
        trait=params.trait,
        meters={"courage": 1.0, "kindness": 1.0},
        memes={"pride": 1.0, "worry": 0.0, "praise": 0.0, "repetition": 0.0, "caution": 0.0},
    )
    helper = Helper(name=params.helper, role="guide")
    problem = Problem(
        thing=params.mishap,
        place=params.city,
        risk="someone could get hurt",
        caution_rule="slow down and check first",
        repetition_line="the plan was repeated until it sounded clear and safe",
    )
    return World(hero=hero, helper=helper, problem=problem, tool=params.tool, city=params.city)


def generate_story(world: World) -> None:
    h = world.hero
    he = world.helper
    p = world.problem

    world.say(f"In {world.city}, {h.name} was a {h.trait} superhero who loved to help.")
    world.say(f"One morning, {h.name} saw {p.thing} near the tallest path in {p.place}, and {h.name} wanted to fix it right away.")
    world.say(f'{he.name} smiled and said, "Good job noticing that. Praise for your quick eyes, {h.name}!"')
    h.memes["praise"] += 1
    h.memes["worry"] += 0.5

    world.say(f"But {he.name} also said, " + f'"{p.caution_rule}. We should use {world.problem.thing} the safe way."')
    h.memes["caution"] += 1
    h.memes["repetition"] += 1
    world.say(f"{h.name} repeated the plan once, then twice: {p.repetition_line}.")

    world.say(f"So {h.name} grabbed {world.tool} and used it carefully, step by step.")
    h.meters["helped"] = 1.0
    h.memes["worry"] = max(0.0, h.memes["worry"] - 0.5)

    world.say(f"{h.name} helped without rushing, and {he.name} gave more praise for the kind choice.")
    h.memes["praise"] += 1
    h.memes["kindness"] += 1
    world.say(f"At the end, {world.problem.thing} was fixed, {world.city} felt safe again, and {h.name} smiled bigger than before.")


def story_qa(world: World) -> list[QAItem]:
    h, he, p = world.hero, world.helper, world.problem
    return [
        QAItem(
            question=f"Who was the superhero in the story?",
            answer=f"The superhero was {h.name}, a {h.trait} hero who wanted to help in {world.city}.",
        ),
        QAItem(
            question=f"Why did {he.name} tell {h.name} to slow down?",
            answer=f"{he.name} wanted {h.name} to be careful, because fixing {p.thing} too fast could mean someone could get hurt.",
        ),
        QAItem(
            question=f"What helped {h.name} stay brave and kind?",
            answer=f"Kind praise helped {h.name} stay brave, and repeating the safe plan helped {h.name} remember what to do.",
        ),
        QAItem(
            question=f"What tool did {h.name} use?",
            answer=f"{h.name} used {world.tool} carefully to help fix the problem.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is praise?",
            answer="Praise is kind words that tell someone they did a good job.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful so you can stay safe.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means saying or doing something again to help remember it.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means helping others and being gentle with them.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a short superhero story for little kids that includes praise, caution, and repetition.",
        f"Tell a gentle story where {world.hero.name} helps with {world.problem.thing} in {world.city} using {world.tool}.",
        "Write a story that shows a hero listening to kind advice, repeating a safe plan, and finishing with praise.",
    ]


def dump_trace(world: World) -> str:
    h = world.hero
    lines = ["--- world model state ---"]
    lines.append(f"hero={h.name} meters={h.meters} memes={h.memes}")
    lines.append(f"helper={world.helper.name} role={world.helper.role}")
    lines.append(f"problem={world.problem.thing} place={world.problem.place}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story QA ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== world QA ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


CURATED = [
    StoryParams("Nova", "Captain Bright", "Sunrise City", "a blocked bridge", "a rope", "brave"),
    StoryParams("Pip", "Aunt Beacon", "Rivergate", "a lost kitten", "a flashlight", "gentle"),
    StoryParams("Zuri", "Coach Star", "Bluebell Town", "a fallen sign", "a ladder", "careful"),
]


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show valid/5."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid/5."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
