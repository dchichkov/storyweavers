#!/usr/bin/env python3
"""
Standalone story world: a folk-tale of trivia, a rotten trouble, and a brave
reconciliation.

The seed words are woven into the world model:
- rotten
- trivia
- sensitive

The story domain is kept small and classical: one child, one elder, one village
setting, one meaningful conflict, and one reconciliation.
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen"}
        male = {"boy", "man", "father", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    mood: str
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
class Trouble:
    id: str
    label: str
    verb: str
    noun: str
    harm: str
    keyword: str
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
class Remedy:
    id: str
    label: str
    method: str
    closing: str
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    trouble: str
    remedy: str
    name: str
    gender: str
    elder: str
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


SETTINGS = {
    "village_square": Setting("the village square", "bright", {"trivia"}),
    "apple_orchard": Setting("the apple orchard", "dappled", {"rotten"}),
    "old_bridge": Setting("the old bridge", "windy", {"trivia", "rotten"}),
}

TROUBLES = {
    "trivia": Trouble(
        id="trivia",
        label="trivia game",
        verb="answer the village trivia",
        noun="trivia",
        harm="wound pride",
        keyword="trivia",
        tags={"trivia"},
    ),
    "rotten": Trouble(
        id="rotten",
        label="rotten crate",
        verb="carry the rotten crate",
        noun="rotten",
        harm="spill the spoil",
        keyword="rotten",
        tags={"rotten"},
    ),
    "sensitive": Trouble(
        id="sensitive",
        label="sensitive matter",
        verb="talk about the sensitive matter",
        noun="sensitive",
        harm="sting hearts",
        keyword="sensitive",
        tags={"sensitive"},
    ),
}

REMEDIES = {
    "apology": Remedy(
        id="apology",
        label="a brave apology",
        method="speak first and say sorry",
        closing="the two of them shared the honey cake",
        tags={"reconciliation", "bravery"},
    ),
    "bridge_help": Remedy(
        id="bridge_help",
        label="a brave hand to help",
        method="cross the bridge together",
        closing="they crossed side by side and laughed again",
        tags={"reconciliation", "bravery"},
    ),
}

NAMES = ["Mira", "Tobin", "Anya", "Pip", "Leif", "Sora"]
TRAITS = ["brave", "gentle", "curious", "kind", "steady", "lively"]
ELDERS = ["grandmother", "grandfather", "aunt", "uncle"]

KNOWLEDGE = {
    "trivia": [
        QAItem(
            question="What is trivia?",
            answer="Trivia is a game of small questions and answers, where people try to remember little facts.",
        )
    ],
    "rotten": [
        QAItem(
            question="What does rotten mean?",
            answer="Rotten means something has gone bad, like fruit or wood that is old and spoiled.",
        )
    ],
    "sensitive": [
        QAItem(
            question="What does sensitive mean?",
            answer="Sensitive means someone feels things deeply and may get hurt by unkind words very easily.",
        )
    ],
    "bravery": [
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing the right thing even when you feel shy, worried, or afraid.",
        )
    ],
    "reconciliation": [
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop fighting, forgive each other, and become friendly again.",
        )
    ],
}


def trouble_risky(setting: Setting, trouble: Trouble) -> bool:
    return trouble.id in setting.affords


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for tid in setting.affords:
            for rid in REMEDIES:
                combos.append((place, tid, rid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world about trivia, rotten trouble, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=ELDERS)
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
    if getattr(args, "place", None) and getattr(args, "trouble", None) and not trouble_risky(_safe_lookup(SETTINGS, getattr(args, "place", None)), _safe_lookup(TROUBLES, getattr(args, "trouble", None))):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, trouble, remedy = rng.choice(valid_combos())
    if getattr(args, "place", None):
        place = getattr(args, "place", None)
    if getattr(args, "trouble", None):
        trouble = getattr(args, "trouble", None)
    if getattr(args, "remedy", None):
        remedy = getattr(args, "remedy", None)
    if not trouble_risky(_safe_lookup(SETTINGS, place), _safe_lookup(TROUBLES, trouble)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    elder = getattr(args, "elder", None) or rng.choice(ELDERS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, trouble=trouble, remedy=remedy, name=name, gender=gender, elder=elder, trait=trait)


def _tell(world: World, hero: Entity, elder: Entity, trouble: Trouble, remedy: Remedy) -> None:
    world.say(
        f"Once in {world.setting.place}, there lived a {hero.pronoun('possessive')} little {hero.type} named {hero.id}. "
        f"{hero.pronoun().capitalize()} was {hero.traits[0]} and loved old stories."
    )
    world.say(
        f"Each evening, {hero.id} and {hero.pronoun('possessive')} {elder.type} listened for news, riddles, and village {trouble.keyword}."
    )
    world.para()
    if trouble.id == "trivia":
        world.say(
            f"One market day, the village held a {trouble.label}. {hero.id} wanted to {trouble.verb}, but {hero.pronoun('possessive')} {elder.type} frowned."
        )
        world.say(
            f"{elder.pronoun().capitalize()} said the {trouble.label} was too important, and {hero.id} felt a sharp sting of pride."
        )
    elif trouble.id == "rotten":
        world.say(
            f"One morning, a {trouble.label} sat by the road, and its smell made the whole lane wrinkle its nose."
        )
        world.say(
            f"{hero.id} wanted to {trouble.verb}, but {hero.pronoun('possessive')} {elder.type} warned that the rotten wood could fall apart."
        )
    else:
        world.say(
            f"One quiet evening, {hero.id} wished to {trouble.verb}, though {hero.pronoun('possessive')} {elder.type} was already tender-hearted about it."
        )
        world.say(
            f"The words were {trouble.noun} and could {trouble.harm}, so the room grew still."
        )
    hero.memes["hurt"] += 1
    elder.memes["worry"] += 1
    world.para()
    world.say(
        f"Still, {hero.id} was brave. {hero.pronoun().capitalize()} took a slow breath, stepped forward, and chose {remedy.label}."
    )
    hero.memes["bravery"] += 1
    elder.memes["soften"] += 1
    world.say(
        f"{hero.id} {remedy.method}, and {hero.pronoun('possessive')} {elder.type} listened."
    )
    hero.memes["reconciliation"] += 1
    elder.memes["reconciliation"] += 1
    world.say(
        f"At last, they made peace. {remedy.closing}, and the night felt warm again."
    )
    world.facts.update(hero=hero, elder=elder, trouble=trouble, remedy=remedy, setting=world.setting)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=[params.trait, "brave"]))
    elder = world.add(Entity(id="Elder", kind="character", type=params.elder, traits=["sensitive", "old"]))
    trouble = _safe_lookup(TROUBLES, params.trouble)
    remedy = _safe_lookup(REMEDIES, params.remedy)
    _tell(world, hero, elder, trouble, remedy)
    story = world.render()
    prompts = [
        f"Write a short folk tale about a child named {hero.id}, a {trouble.keyword} trouble, and a brave reconciliation.",
        f"Tell a gentle story in a village where {hero.id} faces {trouble.label} and fixes it with {remedy.label}.",
        f"Write a child-friendly tale that includes the words rotten, trivia, and sensitive naturally.",
    ]
    story_qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a {hero.traits[0]} little {hero.type}, and {hero.pronoun('possessive')} {elder.type}.",
        ),
        QAItem(
            question=f"What trouble caused the problem?",
            answer=f"The trouble was {trouble.label}, which made the moment tense and hard to say out loud.",
        ),
        QAItem(
            question="How did they become friendly again?",
            answer=f"They became friendly again through {remedy.label}, because {hero.id} was brave enough to begin the peace.",
        ),
    ]
    if trouble.id == "trivia":
        story_qa.append(QAItem(
            question="Why did the elder worry about the trivia game?",
            answer=f"{elder.pronoun().capitalize()} worried because {hero.id} and {hero.pronoun('possessive')} {elder.type} had grown tense over the answers, and the game mattered to the whole village.",
        ))
    if trouble.id == "rotten":
        story_qa.append(QAItem(
            question="What made the rotten trouble dangerous?",
            answer=f"The rotten crate could fall apart, so it was wiser to handle it carefully instead of rushing it.",
        ))
    if trouble.id == "sensitive":
        story_qa.append(QAItem(
            question="Why was the matter sensitive?",
            answer=f"It was sensitive because the words could sting hearts, so everyone had to speak with care.",
        ))
    world_qa = []
    for tag in ["trivia", "rotten", "sensitive", "bravery", "reconciliation"]:
        if tag in KNOWLEDGE:
            world_qa.extend(KNOWLEDGE[tag])
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, dict(e.meters), dict(e.memes))
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"P{i}: {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"WQ: {item.question}")
            print(f"WA: {item.answer}")


ASP_RULES = r"""
place(village_square). place(apple_orchard). place(old_bridge).
trouble(trivia). trouble(rotten). trouble(sensitive).
remedy(apology). remedy(bridge_help).

valid(P,T,R) :- place(P), trouble(T), remedy(R),
                (P = village_square; P = apple_orchard; P = old_bridge).
#show valid/3.
"""


def asp_facts() -> str:
    lines = []
    for p in SETTINGS:
        lines.append(f"place({p}).")
    for t in TROUBLES:
        lines.append(f"trouble({t}).")
    for r in REMEDIES:
        lines.append(f"remedy({r}).")
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch.")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for row in asp_valid():
            print(row)
        return
    rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))
    samples = []
    if getattr(args, "all", None):
        samples = [
            generate(StoryParams(place="village_square", trouble="trivia", remedy="apology", name="Mira", gender="girl", elder="grandmother", trait="brave")),
            generate(StoryParams(place="apple_orchard", trouble="rotten", remedy="bridge_help", name="Tobin", gender="boy", elder="uncle", trait="kind")),
            generate(StoryParams(place="old_bridge", trouble="sensitive", remedy="apology", name="Anya", gender="girl", elder="aunt", trait="steady")),
        ]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < getattr(args, "n", None) * 40:
            i += 1
            try:
                params = resolve_params(args, random.Random(rng.randrange(2**31)))
            except StoryError:
                continue
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
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i+1}" if len(samples) > 1 else "")


if __name__ == "__main__":
    main()
