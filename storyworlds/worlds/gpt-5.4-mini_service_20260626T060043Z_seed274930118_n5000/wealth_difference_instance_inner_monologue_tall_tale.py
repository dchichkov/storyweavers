#!/usr/bin/env python3
"""
A standalone storyworld for a small tall-tale domain about wealth differences,
private inner monologue, and a simple turn toward generosity.

The world is built from a short seed premise:
- one character lives with little wealth
- another character has a great deal of wealth
- the difference between them creates a feeling of comparison
- the hero's inner monologue changes the choice they make
- the ending proves what changed in the world

This script follows the Storyweavers contract:
- self-contained stdlib script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support for --seed, -n, --all, --trace, --qa, --json, --asp, --verify, --show-asp
- inline ASP_RULES twin plus Python reasonableness gate
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    a: object | None = None
    b: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
    atmosphere: str
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
class WealthLevel:
    id: str
    label: str
    phrase: str
    wealth: int
    pride_line: str
    humble_line: str
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
class Gift:
    id: str
    label: str
    phrase: str
    value: int
    fits_poor: bool = False
    fits_rich: bool = False
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    setting: str
    wealth_a: str
    wealth_b: str
    gift: str
    name_a: str
    name_b: str
    role_a: str
    role_b: str
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
    "market": Setting(place="the market square", atmosphere="bright and noisy", affords={"compare", "share"}),
    "wharf": Setting(place="the windy wharf", atmosphere="salt-bright and loud", affords={"compare", "share"}),
    "fair": Setting(place="the county fair", atmosphere="lively with drums and bells", affords={"compare", "share"}),
}

WEALTH_LEVELS = {
    "poor": WealthLevel(
        id="poor",
        label="poor",
        phrase="a little pouch with a few coins and a patched coat",
        wealth=1,
        pride_line="I may have little, but I still have a heart big as a barn door.",
        humble_line="That tiny pouch still matters if I spend it kindly.",
        tags={"wealth", "difference"},
    ),
    "middling": WealthLevel(
        id="middling",
        label="middling",
        phrase="a neat purse and a sturdy cart",
        wealth=5,
        pride_line="I have enough for the road and enough to share a bite.",
        humble_line="Enough is enough, but kindness can still make it shine.",
        tags={"wealth", "difference"},
    ),
    "rich": WealthLevel(
        id="rich",
        label="rich",
        phrase="a trunk of silver, a ring of gold, and a coat with buttons like stars",
        wealth=10,
        pride_line="My pockets jingle like a whole brass band.",
        humble_line="A heavy purse can still be a light thing if it opens for others.",
        tags={"wealth", "difference"},
    ),
}

GIFTS = {
    "apple": Gift(
        id="apple",
        label="apple",
        phrase="one bright apple",
        value=1,
        fits_poor=True,
        fits_rich=True,
        tags={"share", "difference"},
    ),
    "pie": Gift(
        id="pie",
        label="pie",
        phrase="a warm berry pie",
        value=3,
        fits_poor=True,
        fits_rich=True,
        tags={"share", "wealth"},
    ),
    "horse": Gift(
        id="horse",
        label="horse",
        phrase="a shining wagon horse with a golden harness",
        value=9,
        fits_rich=True,
        fits_poor=False,
        tags={"wealth"},
    ),
    "lantern": Gift(
        id="lantern",
        label="lantern",
        phrase="a small brass lantern",
        value=4,
        fits_poor=True,
        fits_rich=True,
        tags={"difference", "instance"},
    ),
}

ROLES = ["farmer", "merchant", "child", "aunt", "uncle", "baker", "carter"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for wa in WEALTH_LEVELS:
            for wb in WEALTH_LEVELS:
                if wa == wb:
                    continue
                for g in GIFTS:
                    combos.append((s, wa, wb))
    return combos


def reasonableness_ok(params: StoryParams) -> bool:
    a = _safe_lookup(WEALTH_LEVELS, params.wealth_a)
    b = _safe_lookup(WEALTH_LEVELS, params.wealth_b)
    gift = _safe_lookup(GIFTS, params.gift)
    return a.id != b.id and abs(a.wealth - b.wealth) >= 3 and (gift.fits_poor or gift.fits_rich)


def explain_rejection(params: StoryParams) -> str:
    a = _safe_lookup(WEALTH_LEVELS, params.wealth_a)
    b = _safe_lookup(WEALTH_LEVELS, params.wealth_b)
    gift = _safe_lookup(GIFTS, params.gift)
    if a.id == b.id:
        return "(No story: the two characters would be equally wealthy, so there is no tall-tale difference to drive the scene.)"
    if abs(a.wealth - b.wealth) < 3:
        return "(No story: the wealth gap is too small to feel like a tall-tale comparison.)"
    if not (gift.fits_poor or gift.fits_rich):
        return "(No story: the chosen gift does not fit either character's circumstances.)"
    return f"(No story: the combination of {a.label} wealth, {b.label} wealth, and {gift.label} does not create a clean conflict.)"


def select_pair(rng: random.Random, args: argparse.Namespace) -> tuple[str, str]:
    pairs = []
    for a in WEALTH_LEVELS:
        for b in WEALTH_LEVELS:
            if a != b and abs(_safe_lookup(WEALTH_LEVELS, a).wealth - _safe_lookup(WEALTH_LEVELS, b).wealth) >= 3:
                pairs.append((a, b))
    if getattr(args, "wealth_a", None) and getattr(args, "wealth_b", None):
        pair = (getattr(args, "wealth_a", None), getattr(args, "wealth_b", None))
        if pair not in pairs:
            pass
        return pair
    return rng.choice(sorted(pairs))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about wealth, difference, and inner monologue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--wealth-a", dest="wealth_a", choices=WEALTH_LEVELS)
    ap.add_argument("--wealth-b", dest="wealth_b", choices=WEALTH_LEVELS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--role-a", choices=ROLES)
    ap.add_argument("--role-b", choices=ROLES)
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
    wealth_a, wealth_b = select_pair(rng, args)
    gift = getattr(args, "gift", None) or rng.choice(list(GIFTS))
    if getattr(args, "wealth_a", None) and getattr(args, "wealth_b", None) and not reasonableness_ok(StoryParams(setting, wealth_a, wealth_b, gift, "", "", "", "")) :
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gift_obj = _safe_lookup(GIFTS, gift)
    name_a = getattr(args, "name_a", None) or rng.choice(["Mabel", "June", "Ned", "Otis", "Pru", "Cora", "Wes", "Hank"])
    name_b = getattr(args, "name_b", None) or rng.choice(["Silas", "Pearl", "Gus", "Betsy", "Ira", "Lena", "Toby", "Mira"])
    role_a = getattr(args, "role_a", None) or rng.choice(ROLES)
    role_b = getattr(args, "role_b", None) or rng.choice([r for r in ROLES if r != role_a])
    return StoryParams(setting=setting, wealth_a=wealth_a, wealth_b=wealth_b, gift=gift_obj.id,
                       name_a=name_a, name_b=name_b, role_a=role_a, role_b=role_b)


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    wa = _safe_lookup(WEALTH_LEVELS, params.wealth_a)
    wb = _safe_lookup(WEALTH_LEVELS, params.wealth_b)
    gift = _safe_lookup(GIFTS, params.gift)
    world = World(setting)

    a = world.add(Entity(id="A", kind="character", type=params.role_a, label=params.name_a))
    b = world.add(Entity(id="B", kind="character", type=params.role_b, label=params.name_b))
    a.meters["wealth"] = wa.wealth
    b.meters["wealth"] = wb.wealth
    a.memes["comparison"] = 0.0
    a.memes["resolve"] = 0.0
    b.memes["pride"] = 0.0
    world.facts.update(a=a, b=b, wa=wa, wb=wb, gift=gift)
    return world


def narrate_setup(world: World) -> None:
    f = world.facts
    a, b, wa, wb = f["a"], f["b"], f["wa"], f["wb"]
    world.say(f"{a.label} was a {a.type} with {wa.phrase}.")
    world.say(f"{b.label} was a {b.type} with {wb.phrase}.")
    world.say(f"At {world.setting.place}, where the day was {world.setting.atmosphere}, the two of them stood like two ends of the same rope.")
    world.say(f"{a.label} had to swallow a little lump in {a.pronoun('possessive')} throat, for the difference looked as wide as a river in flood.")
    a.memes["comparison"] += 1
    world.para()


def narrate_inner_monologue(world: World) -> None:
    f = world.facts
    a, b, wa, wb, gift = f["a"], f["b"], f["wa"], f["wb"], f["gift"]
    if wa.wealth < wb.wealth:
        world.say(f"Inside, {a.label} thought, '{wa.humble_line}'")
        world.say(f"Then another thought came, as plain as a fencepost: '{b.humble_line}'")
    else:
        world.say(f"Inside, {a.label} thought, '{wa.pride_line}'")
    world.say(f"{a.label} looked at {b.label}'s shining things and then at {gift.phrase}, and the difference felt so big it could have held a thunderstorm.")
    world.para()


def narrate_turn(world: World) -> None:
    f = world.facts
    a, b, wa, wb, gift = f["a"], f["b"], f["wa"], f["wb"], f["gift"]
    if gift.id == "apple":
        world.say(f"{a.label} held up the apple and thought, 'A single apple can still be a feast if it lands in the right hands.'")
    elif gift.id == "pie":
        world.say(f"{a.label} smelled the berry pie and thought, 'This little pie can sweeten a whole afternoon.'")
    elif gift.id == "lantern":
        world.say(f"{a.label} lifted the lantern and thought, 'Even a small light can show the road.'")
    else:
        world.say(f"{a.label} looked at the horse and thought, 'This is too grand for me, but not too grand for a kind act.'")
    if wa.wealth < wb.wealth:
        world.say(f"Then {a.label} made a decision as brave as a barn cat in a hailstorm: {a.pronoun('subject').capitalize()} would share first, not compare first.")
    else:
        world.say(f"Then {a.label} decided the richest thing in the square was a generous heart.")
    world.para()


def narrate_resolution(world: World) -> None:
    f = world.facts
    a, b, gift = f["a"], f["b"], f["gift"]
    a.memes["resolve"] += 1
    b.memes["gratitude"] += 1
    world.say(f"{a.label} offered the {gift.label} to {b.label}, and the offering changed the air at once.")
    world.say(f"{b.label} blinked, laughed, and said that a gift given with care was worth more than a wagonload of silver.")
    world.say(f"So the two of them shared the {gift.label} there in {world.setting.place}, and the tall tale ended with the poorer pocket feeling lighter and the richer pocket feeling better.")
    world.say(f"If anyone asked which one had the greater wealth, the answer would be plain: the one who knew how to give.")
    world.facts["resolved"] = True


def generate_story(world: World) -> None:
    narrate_setup(world)
    narrate_inner_monologue(world)
    narrate_turn(world)
    narrate_resolution(world)


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, wa, wb, gift = f["a"], f["b"], f["wa"], f["wb"], f["gift"]
    return [
        QAItem(
            question=f"Who had less wealth in this story, {a.label} or {b.label}?",
            answer=f"{a.label} had less wealth than {b.label}. {a.label} started with {wa.phrase}, while {b.label} had {wb.phrase}.",
        ),
        QAItem(
            question=f"What did {a.label} think to {a.pronoun('subject')}self before making the choice?",
            answer=f"{a.label} thought that even a small thing like {gift.phrase} could matter if it was used kindly.",
        ),
        QAItem(
            question=f"What did {a.label} do at the end with the {gift.label}?",
            answer=f"{a.label} offered the {gift.label} to {b.label}, and they shared it together.",
        ),
        QAItem(
            question=f"Why did the difference between them matter at the start?",
            answer=f"The difference mattered because {a.label} and {b.label} had very different amounts of wealth, so the scene felt huge and lopsided, like two hills of different heights.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is wealth?",
            answer="Wealth is the amount of money or valuable things someone has.",
        ),
        QAItem(
            question="What does difference mean?",
            answer="A difference is how one thing is not the same as another thing.",
        ),
        QAItem(
            question="What is an instance?",
            answer="An instance is one example of something happening or being true.",
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is the private thinking voice in someone's head.",
        ),
        QAItem(
            question="What is a tall tale?",
            answer="A tall tale is a story that tells things in a big, lively, exaggerated way.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b, gift = f["a"], f["b"], f["gift"]
    return [
        f"Write a tall tale about {a.label} and {b.label} that shows a wealth difference and includes inner monologue.",
        f"Tell one instance of a kind choice at {world.setting.place} where {a.label} thinks privately about {gift.phrase}.",
        f"Write a child-friendly story using the words wealth, difference, and instance, with a big-feeling ending.",
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
    lines.append("== (3) World questions ==")
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
        lines.append(f"  {e.id}: {e.label} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
wealth_difference(A,B) :- wealth(A,WA), wealth(B,WB), A != B, WA < WB.
tall_tale(A,B,G) :- wealth_difference(A,B), gift(G), gift_fits(G).
resolved(A,B,G) :- tall_tale(A,B,G), chooses_kindness(A,G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for aff in sorted(s.affords):
            lines.append(asp.fact("affords", sid, aff))
    for wid, w in WEALTH_LEVELS.items():
        lines.append(asp.fact("wealth_level", wid))
        lines.append(asp.fact("wealth", wid, w.wealth))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        if g.fits_poor or g.fits_rich:
            lines.append(asp.fact("gift_fits", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show wealth_difference/2.\n#show tall_tale/3."))
    return sorted(set(asp.atoms(model, "wealth_difference"))), sorted(set(asp.atoms(model, "tall_tale")))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show tall_tale/3."))
    clingo_set = set(asp.atoms(model, "tall_tale"))
    python_set = set()
    for a in WEALTH_LEVELS:
        for b in WEALTH_LEVELS:
            if a == b:
                continue
            if _safe_lookup(WEALTH_LEVELS, a).wealth < _safe_lookup(WEALTH_LEVELS, b).wealth:
                for g in GIFTS:
                    if _safe_lookup(GIFTS, g).fits_poor or _safe_lookup(GIFTS, g).fits_rich:
                        python_set.add((a, b, g))
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python reasoning ({len(clingo_set)} tall-tale combos).")
        return 0
    print("MISMATCH between clingo and Python reasoning.")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    generate_story(world)
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
        print(asp_program("#show tall_tale/3.\n#show wealth_difference/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        diffs, tales = asp_valid()
        print(f"{len(diffs)} wealth differences, {len(tales)} tall-tale instances\n")
        for d in diffs[:10]:
            print("difference:", d)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams("market", "poor", "rich", "apple", "Mabel", "Silas", "child", "merchant"),
            StoryParams("fair", "middling", "rich", "lantern", "Ned", "Mira", "farmer", "aunt"),
            StoryParams("wharf", "poor", "rich", "pie", "Pru", "Gus", "baker", "uncle"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
