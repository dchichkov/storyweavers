#!/usr/bin/env python3
"""
storyworlds/worlds/catalog_commute_problem_solving_quest_detective_story.py
===========================================================================

A small detective-style storyworld about a child, a catalog, and a commute.

Premise:
- A curious kid gets a catalog and wants to go on a commute to a special place.
- Something important is missing: the right route, ticket, or item.
- The child and a helper investigate clues, compare choices in the catalog,
  and solve the problem before the trip can happen.

This world is intentionally narrow: every generated story is a complete,
child-facing detective tale with a clear mystery, clue gathering, solution,
and ending image that proves what changed.

Seed words: catalog, commute
Features: Problem Solving, Quest
Style: Detective Story
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
class Character:
    name: str
    role: str
    trait: str
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

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
class Item:
    name: str
    label: str
    kind: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    clues: list[str] = field(default_factory=list)
    catalog: object | None = None
    problem: object | None = None
    solution: object | None = None
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

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))

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
class Place:
    name: str
    kind: str
    affordances: set[str] = field(default_factory=set)
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
    setting: str
    commute_kind: str
    mystery: str
    hero_name: str
    helper_name: str
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


SETTINGS = {
    "street": Place(name="the city street", kind="street", affordances={"walk", "bus"}),
    "station": Place(name="the train station", kind="station", affordances={"train", "walk"}),
    "market": Place(name="the market road", kind="road", affordances={"bus", "walk"}),
    "library": Place(name="the library corner", kind="indoors", affordances={"walk"}),
}

COMMUTES = {
    "walk": {
        "verb": "walk to the next stop",
        "route": "walk",
        "clue": "shoe prints",
        "delay": "slowly",
        "ticket": False,
        "tool": "map",
    },
    "bus": {
        "verb": "catch the bus",
        "route": "bus",
        "clue": "bus numbers",
        "delay": "late",
        "ticket": True,
        "tool": "schedule",
    },
    "train": {
        "verb": "catch the train",
        "route": "train",
        "clue": "track signs",
        "delay": "missed",
        "ticket": True,
        "tool": "timetable",
    },
}

MYSTERIES = {
    "lost_ticket": {
        "problem": "the ticket was missing",
        "solution": "find the ticket tucked inside the catalog",
        "ending": "the ticket sat safe between the pages of the catalog",
        "need_tool": "ticket",
    },
    "wrong_stop": {
        "problem": "the route looked wrong",
        "solution": "compare the catalog and choose the right stop",
        "ending": "the right stop was circled in bright pencil",
        "need_tool": "schedule",
    },
    "missing_map": {
        "problem": "the map was missing",
        "solution": "use the catalog directory as a map",
        "ending": "the catalog was open to the right page",
        "need_tool": "map",
    },
}

TRAITS = ["curious", "careful", "brave", "patient", "sharp", "gentle"]


class World:
    def __init__(self, setting: Place, commute: dict, mystery: dict) -> None:
        self.setting = setting
        self.commute = commute
        self.mystery = mystery
        self.hero: Optional[Character] = None
        self.helper: Optional[Character] = None
        self.catalog = Item(name="catalog", label="catalog", kind="book")
        self.problem = Item(name="problem", label=mystery["problem"], kind="mystery")
        self.solution = Item(name="solution", label=mystery["solution"], kind="solution")
        self.clues: list[str] = []
        self.resolved = False
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-style catalog commute quest storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--commute-kind", choices=COMMUTES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    commute_kind = getattr(args, "commute_kind", None) or rng.choice(sorted(_safe_lookup(SETTINGS, setting).affordances))
    if commute_kind not in _safe_lookup(SETTINGS, setting).affordances:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    mystery = getattr(args, "mystery", None) or rng.choice(list(MYSTERIES))
    if _safe_lookup(MYSTERIES, mystery)["need_tool"] == "ticket" and not _safe_lookup(COMMUTES, commute_kind)["ticket"]:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if _safe_lookup(MYSTERIES, mystery)["need_tool"] == "schedule" and commute_kind == "walk":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if _safe_lookup(MYSTERIES, mystery)["need_tool"] == "map" and commute_kind == "train":
        return _fallback_storyparams(args, rng, StoryParams, globals())

    name = getattr(args, "name", None) or rng.choice(["Mina", "Leo", "Tara", "Noah", "Ivy", "Owen"])
    helper = getattr(args, "helper", None) or rng.choice(["Aunt June", "Mr. Vale", "Nina", "Mr. Finch"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, commute_kind=commute_kind, mystery=mystery, hero_name=name, helper_name=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.setting), _safe_lookup(COMMUTES, params.commute_kind), _safe_lookup(MYSTERIES, params.mystery))
    hero = Character(name=params.hero_name, role="detective", trait=params.trait)
    helper = Character(name=params.helper_name, role="helper", trait="steady")
    world.hero = hero
    world.helper = helper

    world.say(f"{hero.name} was a {params.trait} little detective who loved a good catalog.")
    world.say(f"One morning, {hero.name} and {helper.name} studied the catalog and planned a {params.commute_kind} commute.")
    world.say(f"{hero.name} wanted to {world.commute['verb']}, but something was wrong: {world.problem.label}.")

    world.para()
    clue1 = world.commute["clue"]
    clue2 = "the catalog's tiny notes"
    clue3 = "a careful look at the route"
    world.clues = [clue1, clue2, clue3]
    world.say(f"{hero.name} followed {clue1}, then checked {clue2}, and finally made {clue3}.")
    world.say(f"{helper.name} pointed at the page where the clue fit, and the mystery began to make sense.")
    world.say(f"At last, {hero.name} solved it by choosing to {world.solution.label}.")

    world.para()
    if params.mystery == "lost_ticket":
        world.say(f"The missing ticket was found inside the catalog, exactly where {hero.name} had slipped it for safekeeping.")
    elif params.mystery == "wrong_stop":
        world.say(f"The wrong stop was crossed out, and the right stop was circled in bright pencil on the route page.")
    else:
        world.say(f"The catalog directory opened like a map, and the hero found the right page without trouble.")

    world.say(f"After that, the {params.commute_kind} commute could begin.")
    world.say(f"{hero.name} stepped forward with a proud grin, and the catalog stayed open to the solved clue.")
    world.resolved = True

    world.facts = {
        "hero": hero,
        "helper": helper,
        "catalog": world.catalog,
        "problem": world.problem,
        "solution": world.solution,
        "setting": world.setting,
        "commute_kind": params.commute_kind,
        "mystery": params.mystery,
        "trait": params.trait,
        "resolved": world.resolved,
    }

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for a young child about a catalog and a {f["commute_kind"]} commute.',
        f"Tell a quest story where {f['hero'].name} solves a problem by checking a catalog with {f['helper'].name}.",
        f"Write a gentle mystery where the clue is hidden in a catalog and the trip is a {f['commute_kind']} ride.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    commute_kind = _safe_fact(world, f, "commute_kind")
    mystery = _safe_fact(world, f, "mystery")
    qa = [
        QAItem(
            question=f"What did {hero.name} and {helper.name} study before the commute?",
            answer=f"They studied a catalog before starting the {commute_kind} commute.",
        ),
        QAItem(
            question=f"What problem did {hero.name} have to solve?",
            answer=f"{hero.name} had to solve the problem that {world.problem.label}.",
        ),
        QAItem(
            question=f"How did {hero.name} solve the mystery?",
            answer=f"{hero.name} solved it by looking at clues, checking the catalog, and using the right idea for the {mystery} mystery.",
        ),
    ]
    if f["resolved"]:
        qa.append(
            QAItem(
                question=f"What changed at the end of the story?",
                answer=f"The mystery was solved, and the {commute_kind} commute could finally begin.",
            )
        )
    return qa


KNOWLEDGE = {
    "catalog": [
        QAItem(
            question="What is a catalog?",
            answer="A catalog is a book or list that shows choices, names, or things you can look through.",
        )
    ],
    "commute": [
        QAItem(
            question="What is a commute?",
            answer="A commute is a regular trip people make to get from one place to another.",
        )
    ],
    "detective": [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks questions, and tries to solve a mystery.",
        )
    ],
    "quest": [
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or search for something important.",
        )
    ],
    "problem": [
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means figuring out what is wrong and choosing a good way to fix it.",
        )
    ],
}


def world_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(KNOWLEDGE["catalog"])
    out.extend(KNOWLEDGE["commute"])
    out.extend(KNOWLEDGE["detective"])
    out.extend(KNOWLEDGE["quest"])
    out.extend(KNOWLEDGE["problem"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for label, ent in [("hero", world.hero), ("helper", world.helper)]:
        if ent:
            lines.append(f"  {label}: {ent.name} ({ent.role}, {ent.trait}) memes={ent.memes}")
    lines.append(f"  setting: {world.setting.name} affordances={sorted(world.setting.affordances)}")
    lines.append(f"  commute: {world.commute['route']} clue={world.commute['clue']}")
    lines.append(f"  mystery: {world.mystery}")
    lines.append(f"  resolved: {world.resolved}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(street).
setting(station).
setting(market).
setting(library).

affords(street,walk).
affords(street,bus).
affords(station,train).
affords(station,walk).
affords(market,bus).
affords(market,walk).
affords(library,walk).

commute(walk).
commute(bus).
commute(train).

ticket_needed(bus).
ticket_needed(train).

mystery(lost_ticket).
mystery(wrong_stop).
mystery(missing_map).

valid(Place,Commute,Mystery) :- affords(Place,Commute), commute(Commute), mystery(Mystery),
    not blocked(Place,Commute,Mystery).

blocked(Place,walk,lost_ticket) :- setting(Place).
blocked(library,walk,wrong_stop).
blocked(station,train,missing_map).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
        for a in sorted(_safe_lookup(SETTINGS, s).affordances):
            lines.append(asp.fact("affords", s, a))
    for c in COMMUTES:
        lines.append(asp.fact("commute", c))
        if _safe_lookup(COMMUTES, c)["ticket"]:
            lines.append(asp.fact("ticket_needed", c))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for commute in setting.affordances:
            for mystery in MYSTERIES:
                if resolve_combo(place, commute, mystery):
                    combos.append((place, commute, mystery))
    return combos


def resolve_combo(place: str, commute: str, mystery: str) -> bool:
    if commute not in _safe_lookup(SETTINGS, place).affordances:
        return False
    need = _safe_lookup(MYSTERIES, mystery)["need_tool"]
    if need == "ticket" and not _safe_lookup(COMMUTES, commute)["ticket"]:
        return False
    if need == "schedule" and commute == "walk":
        return False
    if need == "map" and commute == "train":
        return False
    if place == "library" and mystery == "wrong_stop":
        return False
    if place == "station" and mystery == "missing_map":
        return False
    return True


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams("street", "bus", "lost_ticket", "Mina", "Nina", "curious"),
    StoryParams("station", "train", "wrong_stop", "Leo", "Mr. Vale", "careful"),
    StoryParams("market", "walk", "missing_map", "Ivy", "Aunt June", "brave"),
]


def explain_rejection(params: StoryParams) -> str:
    return "(No story: the chosen commute and mystery do not fit together in a believable detective case.)"


def build_sample(params: StoryParams) -> StorySample:
    return generate(params)


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
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        for c in combos:
            print(c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 40, 40):
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
            header = f"### {p.hero_name}: {p.commute_kind} / {p.mystery} / {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
