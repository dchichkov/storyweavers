#!/usr/bin/env python3
"""
A rhyming storyworld about a kennel, kindness, a tricky problem, and a small sacrifice.

The premise:
- A child visits a kennel and notices that one timid puppy cannot rest because a blanket is missing.
- The child wants something simple and shiny for the day, but sees the puppy needs it more.

The turn:
- A guard or caretaker explains the problem: the kennel is cold, one crate is drafty, and the smallest puppy keeps shivering.
- The child faces a choice between keeping a prized item and giving it up to help.

The resolution:
- The child makes a gentle sacrifice, uses problem solving to improve the kennel, and the puppy settles happily.
- The ending proves the change with a warmer kennel and a calmer, grateful pup.

The style aims for a short, child-facing rhyming tale with a clear beginning,
middle turn, and ending image.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    prize: object | None = None
    pup: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            gender = self.meters.get("gender", 0)
            if gender == 1:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if gender == 2:
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
    place: str = "the kennel"
    indoors: bool = True
    drafty_spots: set[str] = field(default_factory=lambda: {"crate"})
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
class Hero:
    name: str
    gender: str
    trait: str
    rhyme_word: str
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
    item: str
    missing: str
    cold_spot: str
    discomfort: str
    clue: str
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
class Sacrifice:
    prized_item: str
    helps_with: str
    action: str
    reward_image: str
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
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None
    params: object | None = None
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kennel": Setting(place="the kennel", indoors=True),
}

HERO_TRAITS = ["kind", "brave", "gentle", "curious", "thoughtful"]

PROBLEMS = {
    "blanket": Problem(
        item="blanket",
        missing="missing a blanket",
        cold_spot="the drafty crate",
        discomfort="shivered in the chill",
        clue="a cold nose and a tiny whimper",
    ),
    "bowl": Problem(
        item="water bowl",
        missing="too far from the smallest pup",
        cold_spot="the back corner",
        discomfort="pattered and pawed in worry",
        clue="an empty gulp and a thirsty look",
    ),
    "toy": Problem(
        item="toy rope",
        missing="tangled by the gate",
        cold_spot="the hallway floor",
        discomfort="waited sadly in the hush",
        clue="a bored yawn and a droopy tail",
    ),
}

SACRIFICES = {
    "scarf": Sacrifice(
        prized_item="a warm red scarf",
        helps_with="the cold draft",
        action="gave up the scarf to wrap the crate",
        reward_image="the crate looked snug and neat",
    ),
    "cookie": Sacrifice(
        prized_item="a sweet star cookie",
        helps_with="the hungry pup",
        action="shared the cookie with the smallest dog",
        reward_image="the pup licked crumbs from a happy mouth",
    ),
    "pin": Sacrifice(
        prized_item="a shiny hair pin",
        helps_with="the loose rope",
        action="traded the pin for a clip that tied the rope",
        reward_image="the toy stayed tidy by the gate",
    ),
}

RHYMES = {
    "kind": "in a cheerful, helpful kind",
    "brave": "with a steady, brave mind",
    "gentle": "in a soft and gentle way",
    "curious": "to see what they could make okay",
    "thoughtful": "with a thoughtful, clever plan",
}


# ---------------------------------------------------------------------------
# Inline ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show problem/1.
#show sacrifice/1.
#show resolved/1.

problem(blanket).
problem(bowl).
problem(toy).

sacrifice(scarf).
sacrifice(cookie).
sacrifice(pin).

resolved(blanket) :- sacrifice(scarf).
resolved(bowl) :- sacrifice(cookie).
resolved(toy) :- sacrifice(pin).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for sid in SACRIFICES:
        lines.append(asp.fact("sacrifice", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    return [("kennel", pid) for pid in PROBLEMS]


def select_solution(problem_id: str) -> tuple[str, Sacrifice]:
    if problem_id == "blanket":
        return "sacrifice", SACRIFICES["scarf"]
    if problem_id == "bowl":
        return "sharing", SACRIFICES["cookie"]
    if problem_id == "toy":
        return "problem solving", SACRIFICES["pin"]
    pass


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def tell(hero: Hero, problem: Problem, sacrifice: Sacrifice) -> World:
    world = World()
    setting = SETTINGS["kennel"]

    child = world.add(Entity(
        id=hero.name,
        kind="character",
        meters={"gender": 1 if hero.gender == "girl" else 2},
    ))
    pup = world.add(Entity(id="pup", kind="character", label="the smallest puppy"))
    caretaker = world.add(Entity(id="caretaker", kind="character", label="the kennel keeper"))
    prize = world.add(Entity(
        id="prize",
        kind="thing",
        label=sacrifice.prized_item,
        phrase=sacrifice.prized_item,
        owner=child.id,
        caretaker=child.id,
    ))

    world.say(
        f"{hero.name} came to {setting.place} {_safe_lookup(RHYMES, hero.trait)}, "
        f"where soft paws pattered and sleepy tails lined."
    )
    world.say(
        f"{hero.name} liked the little dogs and liked the warm sight, "
        f"and wore {prize.phrase} so bright and light."
    )

    world.para()
    world.say(
        f"But in the back crate there was a small, sad sign: "
        f"the pup was {problem.discomfort}, and the clue was plain to find."
    )
    world.say(
        f"The kennel keeper said, 'That crate needs help today; "
        f"the draft slips in, and it cannot stay.'"
    )

    world.para()
    world.say(
        f"{hero.name} saw the trouble and thought with care, "
        f"then used {hero.pronoun('possessive')} best idea right there."
    )
    world.say(
        f"{hero.name} noticed that {sacrifice.action}, "
        f"and that simple choice could brighten the scene."
    )
    world.say(
        f"With kind hands and a clever plan, {hero.name} fixed the need, "
        f"and gave up the prize to do the good deed."
    )

    child.memes["kindness"] = 2
    child.memes["problem_solving"] = 2
    child.memes["sacrifice"] = 1
    pup.meters["comfort"] = 2
    caretaker.meters["relief"] = 1
    world.facts = {
        "hero": hero,
        "problem": problem,
        "sacrifice": sacrifice,
        "setting": setting,
        "child": child,
        "pup": pup,
        "caretaker": caretaker,
    }

    world.para()
    world.say(
        f"Now the kennel felt snug, and the pup gave a grin; "
        f"the cold spot was calmer, the warmth tucked in."
    )
    world.say(
        f"{hero.name} smiled at the ending, proud and still, "
        f"for kindness can shine when it answers a need with skill."
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Hero = _safe_fact(world, f, "hero")
    problem: Problem = _safe_fact(world, f, "problem")
    sacrifice: Sacrifice = _safe_fact(world, f, "sacrifice")
    return [
        f'Write a short rhyming story for a small child about a kennel, {problem.item}, and a kind sacrifice.',
        f"Tell a gentle story where {hero.name} goes to the kennel, notices {problem.missing}, and solves it with {sacrifice.prized_item}.",
        "Write a simple rhyming tale that begins with a cozy kennel and ends with kindness making the problem better.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Hero = _safe_fact(world, f, "hero")
    problem: Problem = _safe_fact(world, f, "problem")
    sacrifice: Sacrifice = _safe_fact(world, f, "sacrifice")
    return [
        QAItem(
            question=f"What did {hero.name} notice first at the kennel?",
            answer=f"{hero.name} noticed that the {problem.item} was {problem.missing}, and the puppy was uncomfortable in the drafty crate.",
        ),
        QAItem(
            question=f"What did {hero.name} give up to help?",
            answer=f"{hero.name} gave up {sacrifice.prized_item} so the kennel problem could be fixed with kindness and care.",
        ),
        QAItem(
            question=f"How was the problem solved?",
            answer=f"{hero.name} used a careful plan and a small sacrifice to help the puppy, which solved the problem and made the kennel warmer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a kennel?",
            answer="A kennel is a place where dogs stay, rest, and get care.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring about someone else's needs.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means looking carefully at a trouble and choosing a plan that helps fix it.",
        ),
        QAItem(
            question="What does sacrifice mean?",
            answer="A sacrifice is when you give up something you want so you can help someone else.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: kind={e.kind} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP helpers / verify
# ---------------------------------------------------------------------------
def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show problem/1.\n#show sacrifice/1."))
    return sorted(set(asp.atoms(model, "problem")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    model = asp.one_model(asp_program("#show problem/1."))
    asp_set = set(asp.atoms(model, "problem"))
    if {p for _, p in py} == {p[0] for p in asp_set}:
        print("OK: ASP and Python agree on the problem registry.")
        return 0
    print("Mismatch between ASP and Python.")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld: kennel, kindness, sacrifice, and problem solving.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=HERO_TRAITS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--problem", choices=PROBLEMS)
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name_choices = ["Mia", "Lily", "Noah", "Theo", "Ava", "Ben"]
    trait = getattr(args, "trait", None) or rng.choice(HERO_TRAITS)
    name = getattr(args, "name", None) or rng.choice(name_choices)
    if getattr(args, "problem", None) and getattr(args, "problem", None) not in PROBLEMS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(name=name, gender=gender, trait=trait, seed=getattr(args, "seed", None))


def generate(params: StoryParams) -> StorySample:
    problem_id = "blanket"
    if params.name.lower().startswith("n"):
        problem_id = "bowl"
    elif params.name.lower().startswith("t"):
        problem_id = "toy"
    problem = _safe_lookup(PROBLEMS, problem_id)
    sacrifice = {
        "blanket": SACRIFICES["scarf"],
        "bowl": SACRIFICES["cookie"],
        "toy": SACRIFICES["pin"],
    }[problem_id]
    hero = Hero(
        name=params.name,
        gender=params.gender,
        trait=params.trait,
        rhyme_word=_safe_lookup(RHYMES, params.trait),
    )
    world = tell(hero, problem, sacrifice)
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
        print(asp_program("#show problem/1.\n#show sacrifice/1.\n#show resolved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show resolved/1."))
        print("\n".join(str(x) for x in model))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for i, pid in enumerate(PROBLEMS):
            params = StoryParams(
                name=["Mia", "Noah", "Ava"][i % 3],
                gender=["girl", "boy", "girl"][i % 3],
                trait=_safe_lookup(HERO_TRAITS, i % len(HERO_TRAITS)),
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
