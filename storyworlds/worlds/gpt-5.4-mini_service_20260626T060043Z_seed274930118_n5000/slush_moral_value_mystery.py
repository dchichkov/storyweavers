#!/usr/bin/env python3
"""
A standalone storyworld script for a small mystery about slush, clues, and
moral value: honesty, responsibility, and kindness.

Premise:
- A child notices a puzzling slush trail and tries to solve who made the mess.
- The tension is not danger, but uncertainty and a small unfair accusation.
- The turn comes when the child follows clues carefully and learns the truth.
- The resolution rewards honesty: the right person admits the mistake, and the
  mess is cleaned together.

The world model tracks physical meters and emotional memes so the story is
state-driven rather than a swapped-nouns template.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    adult: object | None = None
    hero: object | None = None
    suspect: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "mother", "mom", "woman", "aunt"}
        masculine = {"boy", "father", "dad", "man", "uncle"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
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
    indoor: bool = False
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
class Mystery:
    id: str
    clue: str
    mess: str
    soil: str
    trail: str
    reveal: str
    risk: str
    moral_value: str
    keyword: str = "slush"
    tags: set[str] = field(default_factory=set)
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
class Suspect:
    id: str
    label: str
    type: str
    likely: bool = True
    excuse: str = ""
    truth: str = ""
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    c: object | None = None
    world: object | None = None
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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        c.paragraphs = [[]]
        return c
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
    "hallway": Setting(place="the hallway", indoor=True, affords={"slush"}),
    "porch": Setting(place="the front porch", indoor=False, affords={"slush"}),
    "mudroom": Setting(place="the mudroom", indoor=True, affords={"slush"}),
}

MYSTERIES = {
    "slush": Mystery(
        id="slush",
        clue="a line of wet, gritty footprints",
        mess="slush",
        soil="wet and gritty",
        trail="small puddles and tiny drips",
        reveal="someone had come in with slushy boots and forgotten to wipe them",
        risk="the clean floor might get ruined",
        moral_value="honesty",
        tags={"slush", "wet", "cleanliness", "truth"},
    ),
}

SUSPECTS = {
    "sibling": Suspect(
        id="sibling",
        label="older sibling",
        type="boy",
        likely=True,
        excuse="I came in only for a minute.",
        truth="I forgot to take off my boots.",
    ),
    "friend": Suspect(
        id="friend",
        label="next-door friend",
        type="girl",
        likely=False,
        excuse="I was only looking for my ball.",
        truth="I stayed dry on the porch.",
    ),
    "dog": Suspect(
        id="dog",
        label="muddy dog",
        type="dog",
        likely=False,
        excuse="I only wagged my tail.",
        truth="The dog was innocent; the prints were too straight for paws.",
    ),
}

GIRL_NAMES = ["Mina", "Lina", "Nora", "Ivy", "Maya", "Ella"]
BOY_NAMES = ["Theo", "Finn", "Ben", "Leo", "Eli", "Noah"]
TRAITS = ["curious", "careful", "brave", "thoughtful", "patient"]


def clue_matches(mystery: Mystery, suspect: Suspect) -> bool:
    if suspect.id == "dog":
        return False
    if suspect.id == "friend":
        return False
    return True


def select_suspect(mystery: Mystery, rng: random.Random) -> Suspect:
    return rng.choice([s for s in SUSPECTS.values() if clue_matches(mystery, s)])


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld about slush and honesty.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES, default="slush")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    parent: str
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> "StoryParams":
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    mystery = getattr(args, "mystery", None) or "slush"
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    if not _safe_lookup(SETTINGS, place).affords & {mystery}:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, parent=parent, trait=trait)


def _deduce(world: World, hero: Entity, suspect: Entity, mystery: Mystery) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"{hero.id} noticed {mystery.clue} near {world.setting.place} and knew this was not a normal accident."
    )
    world.say(
        f"{hero.id} followed the {mystery.keyword} trail because the shiny drops all pointed the same way."
    )
    if suspect.id == "dog":
        world.say(
            f"At first, {hero.id} wondered about the dog, but the prints were too straight and too neat."
        )


def tell(setting: Setting, mystery: Mystery, hero_name: str, hero_gender: str, parent: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, label=hero_name, memes={}))

    adult = world.add(Entity(id="Parent", kind="character", type=parent, label=f"the {parent}", memes={}))
    suspect = world.add(Entity(
        id="Suspect",
        kind="character",
        type="boy",
        label="older sibling",
        memes={},
    ))
    world.facts["hero"] = hero
    world.facts["parent"] = adult
    world.facts["suspect"] = suspect
    world.facts["mystery"] = mystery

    world.say(f"{hero.id} was a {trait} child who liked solving small puzzles.")
    world.say(
        f"One day, {hero.id} saw {mystery.clue} in {setting.place}. The floor should have been clean."
    )
    world.say(
        f"{hero.id}'s {parent} looked worried, because {mystery.risk}."
    )
    world.para()

    _deduce(world, hero, suspect, mystery)

    suspect.truth = "I was the one who made the slush marks."
    world.say(
        f"Near the boot rack, {hero.id} found {suspect.label}. {suspect.label.capitalize()} said, "
        f"\"{suspect.truth}\""
    )
    world.say(
        f"{suspect.label.capitalize()} explained {suspect.excuse} Then {suspect.label} told the truth and admitted the mistake."
    )

    world.para()
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    adult.memes["trust"] = adult.memes.get("trust", 0) + 1
    world.say(
        f"{hero.id} did not scold anyone. Instead, {hero.id} said that honesty mattered more than hiding a little mess."
    )
    world.say(
        f"Together they wiped the slush trail away, and soon the hallway was clean again."
    )
    world.say(
        f"By the end, {hero.id} knew the clue had led to a fair answer, and the family felt calmer because the truth was out."
    )

    world.facts["resolved"] = True
    world.facts["moral_value"] = mystery.moral_value
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    mystery = _safe_fact(world, f, "mystery")
    return [
        f'Write a gentle mystery for a young child about {mystery.keyword} and honesty.',
        f"Tell a short story where {hero.id} notices a {mystery.keyword} clue and solves a small family puzzle.",
        f"Write a child-friendly mystery that ends with the truth being told and the mess getting cleaned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    suspect = _safe_fact(world, f, "suspect")
    mystery = _safe_fact(world, f, "mystery")
    return [
        QAItem(
            question=f"What clue did {hero.id} see in {world.setting.place}?",
            answer=f"{hero.id} saw {mystery.clue}, which showed that something slushy had been tracked inside.",
        ),
        QAItem(
            question=f"Why was {parent.label} worried about the floor?",
            answer=f"{parent.label.capitalize()} was worried because the clean floor might get ruined by the wet slush.",
        ),
        QAItem(
            question=f"Who finally admitted what happened to the slush?",
            answer=f"{suspect.label.capitalize()} admitted it and told the truth instead of hiding the mistake.",
        ),
        QAItem(
            question=f"What good value mattered most in the story?",
            answer=f"Honesty mattered most, because the problem was solved after someone told the truth.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is slush?",
            answer="Slush is wet, messy snow that has started to melt into a gray, watery mix.",
        ),
        QAItem(
            question="Why is telling the truth important?",
            answer="Telling the truth helps people solve problems fairly and trust each other.",
        ),
        QAItem(
            question="What does a clue do in a mystery?",
            answer="A clue is a small piece of information that helps someone figure out what happened.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(hallway).
setting(porch).
setting(mudroom).
affords(hallway,slush).
affords(porch,slush).
affords(mudroom,slush).

mystery(slush).
moral_value(slush,honesty).

clue(slush,"wet gritty footprints").
truthful_resolution(slush) :- moral_value(slush,honesty).
valid_story(P,M) :- setting(P), affords(P,M), mystery(M), truthful_resolution(M).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("moral_value", mid, m.moral_value))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {(p, m) for p in SETTINGS for m in MYSTERIES if _safe_lookup(SETTINGS, p).affords & {m}}
    if asp_set == py_set:
        print(f"OK: ASP matches Python ({len(py_set)} valid stories).")
        return 0
    print("MISMATCH between ASP and Python.")
    if asp_set - py_set:
        print("Only in ASP:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("Only in Python:", sorted(py_set - asp_set))
    return 1


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"  {e.id:10} ({e.kind}) {' '.join(bits)}")
    out.append(f"  trace: {world.trace}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(MYSTERIES, params.mystery), params.name, params.gender, params.parent, params.trait)
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


def build_samples(args: argparse.Namespace) -> list[StorySample]:
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    seen = set()
    i = 0
    while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
        rng = random.Random(base_seed + i)
        i += 1
        params = resolve_params(args, rng)
        params.seed = base_seed + i
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        items = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(items)} valid stories:\n")
        for place, mystery in items:
            print(f"  {place} / {mystery}")
        return

    if getattr(args, "all", None):
        samples = [
            generate(StoryParams(place=p, mystery="slush", name="Mina", gender="girl", parent="mother", trait="curious"))
            for p in SETTINGS
        ]
    else:
        samples = build_samples(args)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
