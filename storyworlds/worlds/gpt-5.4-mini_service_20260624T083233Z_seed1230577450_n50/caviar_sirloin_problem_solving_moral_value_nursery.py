#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T083233Z_seed1230577450_n50/caviar_sirloin_problem_solving_moral_value_nursery.py
==============================================================================================================================

A tiny nursery-rhyme storyworld about a small feast, a tricky mismatch, and a
kind fix. The seed tale suggests two rich foods -- caviar and sirloin -- and the
world turns that into a child-facing problem-solving story with a moral value:
share fairly, speak honestly, and use a clever plan.

The story is generated from a simulated world state, not from a frozen template.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    traits: list = field(default_factory=list)
    child: object | None = None
    dish1: object | None = None
    dish2: object | None = None
    guard: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
        if not hasattr(self, "_tags"):
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
    indoors: bool
    affords: set[str] = field(default_factory=set)
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Food:
    id: str
    label: str
    phrase: str
    kind: str
    region: str
    value: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
        self.problem: str = ""
        self.solution: str = ""

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.problem = self.problem
        clone.solution = self.solution
        return clone


SETTINGS = {
    "nursery": Setting(place="the nursery", indoors=True, affords={"mix"}),
    "table": Setting(place="the little table", indoors=True, affords={"mix"}),
    "garden": Setting(place="the garden nook", indoors=False, affords={"mix"}),
}

FOODS = {
    "caviar": Food(
        id="caviar",
        label="caviar",
        phrase="a little dish of caviar",
        kind="caviar",
        region="table",
        value="fancy",
        tags={"caviar", "salt"},
    ),
    "sirloin": Food(
        id="sirloin",
        label="sirloin",
        phrase="a small plate of sirloin",
        kind="sirloin",
        region="table",
        value="warm",
        tags={"sirloin", "savory"},
    ),
}

FIXES = {
    "share": Fix(
        id="share",
        label="sharing spoon",
        prep="split the feast into two neat bites",
        tail="shared the feast with a tidy little plan",
        helps={"caviar", "sirloin"},
        covers={"table"},
    ),
    "stew": Fix(
        id="stew",
        label="little stew bowl",
        prep="turn the problem into a gentle stew",
        tail="made a warm stew to save the day",
        helps={"sirloin"},
        covers={"table"},
    ),
}

NAMES = ["Mimi", "Toby", "Lily", "Milo", "Nina", "Pip"]
TRAITS = ["tiny", "cheerful", "careful", "curious", "brave"]
GUARDIANS = ["mother", "father", "grandma", "grandpa"]


@dataclass
class StoryParams:
    place: str
    food_one: str
    food_two: str
    name: str
    trait: str
    guardian: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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


def prize_pair_ok(food_one: Food, food_two: Food) -> bool:
    return food_one.kind != food_two.kind


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        if "mix" not in setting.affords:
            continue
        for one in FOODS:
            for two in FOODS:
                if one != two:
                    combos.append((place, one, two))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about caviar and sirloin.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--food-one", choices=FOODS)
    ap.add_argument("--food-two", choices=FOODS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--guardian", choices=GUARDIANS)
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
    if getattr(args, "food_one", None) and getattr(args, "food_two", None) and getattr(args, "food_one", None) == getattr(args, "food_two", None):
        return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "food_one", None) is None or c[1] == getattr(args, "food_one", None))
              and (getattr(args, "food_two", None) is None or c[2] == getattr(args, "food_two", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, one, two = rng.choice(list(combos))
    return StoryParams(
        place=place,
        food_one=one,
        food_two=two,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
        guardian=getattr(args, "guardian", None) or rng.choice(GUARDIANS),
    )


def _mix(world: World, child: Entity, one: Food, two: Food) -> None:
    child.memes["desire"] += 1
    child.meters["hunger"] += 1
    if one.kind == "caviar" and two.kind == "sirloin":
        child.memes["confused"] += 1
        world.problem = "a fancy mismatch"
        world.solution = "a sharing plan"
    else:
        world.problem = "a little kitchen puzzle"
        world.solution = "a careful plan"


def tell(setting: Setting, one: Food, two: Food, name: str, trait: str, guardian: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type="child", label=name, traits=[trait] if False else []))
    guard = world.add(Entity(id=guardian, kind="character", type=guardian, label=guardian))
    dish1 = world.add(Entity(id=one.id, type=one.kind, label=one.label, phrase=one.phrase, owner=name))
    dish2 = world.add(Entity(id=two.id, type=two.kind, label=two.label, phrase=two.phrase, owner=name))

    child.memes["joy"] += 1
    world.say(f"{name} was a {trait} little child who liked to hum and play.")
    world.say(f"{name} had {dish1.phrase} and {dish2.phrase}, all set out on a tray.")
    world.para()

    world.say(f"In {setting.place}, the day was bright and small.")
    world.say(f"But {name} wanted to mix the feast in a nursery rhyme-y call.")
    _mix(world, child, one, two)
    world.say(f"{name} peeked at the two dishes and said, “Oh dear, oh dear, what now?”")
    world.say(f"{guardian} saw the tangle and said, “Let us think this through somehow.”")

    world.para()
    if one.kind == "caviar" and two.kind == "sirloin":
        child.memes["worry"] += 1
        world.say(f"The caviar was tiny and fancy, the sirloin warm and brave.")
        world.say(f"They did not belong in one big heap, like a wave on top of a wave.")
        fix = FIXES["share"]
        world.say(f'"How about we {fix.prep}," said {guardian}, with a calm and kindly grin.')
        child.memes["trust"] += 1
        child.memes["worry"] = 0
        child.memes["kindness"] += 1
        world.say(f'{name} nodded and chose the sharing spoon to tuck the feast back in.')
        world.say(f"They {fix.tail}, and each got a fair and happy share.")
        world.say(f"Then {name} smiled at {guardian}, with crumbs and care in the air.")
    else:
        fix = FIXES["stew"]
        world.say(f"The little puzzle was solved with care, with not a crumb to flee.")
        world.say(f"They used a gentle bowl and plan, as neat as a plan could be.")
        world.say(f"{name} felt proud for helping out, and {guardian} felt proud too.")
        world.say(f"The supper stayed warm, and the night felt bright and new.")

    world.facts.update(
        child=child,
        guardian=guard,
        food_one=dish1,
        food_two=dish2,
        fix=fix,
        setting=setting,
        trait=trait,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short nursery-rhyme story for a small child about {f["child"].id}, {f["food_one"].label}, and {f["food_two"].label}.',
        f"Tell a sweet story where a {f['trait']} little child solves a food puzzle at {f['setting'].place}.",
        "Write a gentle rhyme about a problem, a clever fix, and a kind moral value.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    guardian: Entity = f["guardian"]
    food_one: Entity = f["food_one"]
    food_two: Entity = f["food_two"]
    fix: Fix = f["fix"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {child.id}, a {f['trait']} little child, and {guardian.id}, who helped with the feast.",
        ),
        QAItem(
            question=f"What two foods caused the puzzle?",
            answer=f"The puzzle came from {food_one.label} and {food_two.label}, which needed a clever plan.",
        ),
        QAItem(
            question=f"How was the problem solved?",
            answer=f"They solved it by using {fix.label} and making a fair, careful plan.",
        ),
        QAItem(
            question=f"What kind value does the story teach?",
            answer="It teaches kindness and sharing, because the best fix was the one that was fair to everyone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(question="What is caviar?", answer="Caviar is tiny fish eggs often served as a fancy food."),
        QAItem(question="What is sirloin?", answer="Sirloin is a cut of beef, often cooked as a steak."),
        QAItem(question="What does it mean to share?", answer="To share means to give some of what you have to someone else."),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="nursery", food_one="caviar", food_two="sirloin", name="Mimi", trait="cheerful", guardian="mother"),
    StoryParams(place="table", food_one="caviar", food_two="sirloin", name="Pip", trait="curious", guardian="father"),
]


ASP_RULES = r"""
food(caviar).
food(sirloin).
place(nursery).
place(table).
place(garden).
affords(nursery,mix).
affords(table,mix).
affords(garden,mix).
compatible(P,F1,F2) :- affords(P,mix), food(F1), food(F2), F1 != F2.
#show compatible/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for fid in FOODS:
        lines.append(asp.fact("food", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


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


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(FOODS, params.food_one), _safe_lookup(FOODS, params.food_two),
                 params.name, params.trait, params.guardian)
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
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            i += 1
            seed = base_seed + i
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
            header = f"### {p.name}: {p.food_one} and {p.food_two} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
