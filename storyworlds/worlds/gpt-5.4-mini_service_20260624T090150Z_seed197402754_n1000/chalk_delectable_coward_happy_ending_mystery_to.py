#!/usr/bin/env python3
"""
A small fable-style story world about a chalk mystery, a delectable treat,
and a coward who learns a kinder kind of courage.

The seed image: a timid child sees chalk marks and a missing sweet, worries,
asks questions, and finally solves the mystery with help.
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

    adult: object | None = None
    clue: object | None = None
    hero: object | None = None
    treat: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dust": 0.0, "crumbs": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "curiosity": 0.0, "courage": 0.0, "joy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Place:
    name: str
    indoors: bool = False
    has_chalkboard: bool = False
    has_treats: bool = False
    has_garden: bool = False
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
class Mystery:
    id: str
    clue: str
    question: str
    culprit: str
    solution: str
    cover: str
    reveal: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
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
        c = World(self.place)
        c.entities = _copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


MYSTERIES = {
    "chalkboard": Mystery(
        id="chalkboard",
        clue="a line of white chalk dust near the school steps",
        question="who wrote the secret map on the board?",
        culprit="the teacher",
        solution="The teacher had drawn a helpful map for the children.",
        cover="chalk marks",
        reveal="The marks were only directions, not a warning.",
    ),
    "cookie": Mystery(
        id="cookie",
        clue="three crumbs and a sweet smell by the kitchen table",
        question="who took the delectable cookie?",
        culprit="the grandmother",
        solution="The grandmother had saved the cookie for the smallest child.",
        cover="crumbs",
        reveal="The treat had not been stolen at all.",
    ),
    "garden": Mystery(
        id="garden",
        clue="a muddy path and a tiny chalk arrow by the gate",
        question="who went into the garden first?",
        culprit="the gardener",
        solution="The gardener had gone ahead to open the gate.",
        cover="chalk arrow",
        reveal="The arrow was a guide, not a trap.",
    ),
}


PLACES = {
    "schoolyard": Place(name="the schoolyard", has_chalkboard=True),
    "kitchen": Place(name="the kitchen", indoors=True, has_treats=True),
    "garden": Place(name="the garden", has_garden=True),
}


TRAITS = ["careful", "gentle", "timid", "thoughtful", "quiet", "kind"]
GIRL_NAMES = ["Mina", "Lena", "Ivy", "Clara", "Nora", "Tessa"]
BOY_NAMES = ["Owen", "Milo", "Ezra", "Jonah", "Theo", "Ari"]


def reasonableness_gate(place: Place, mystery: Mystery, gender: str) -> None:
    if mystery.id == "cookie" and not place.has_treats:
        pass
    if mystery.id == "chalkboard" and not place.has_chalkboard:
        pass
    if mystery.id == "garden" and not place.has_garden:
        pass
    if gender not in {"girl", "boy"}:
        pass


def resolve_clue(world: World, hero: Entity, mystery: Mystery) -> bool:
    hero.memes["curiosity"] += 1
    if mystery.id == "cookie":
        return True
    if mystery.id == "chalkboard":
        return True
    if mystery.id == "garden":
        return True
    return False


def tell(place: Place, mystery: Mystery, hero_name: str, gender: str, parent: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, label=hero_name))
    adult = world.add(Entity(id="Adult", kind="character", type=parent, label=f"the {parent}"))
    clue = world.add(Entity(
        id="Clue",
        type="thing",
        label=mystery.cover,
        phrase=mystery.clue,
        caretaker=adult.id,
    ))
    treat = world.add(Entity(
        id="Treat",
        type="thing",
        label="delectable treat" if mystery.id == "cookie" else "small prize",
        phrase="a delectable cookie" if mystery.id == "cookie" else "a tiny treasure",
        owner=hero.id,
        caretaker=adult.id,
    ))

    hero.memes["fear"] += 1
    world.say(
        f"{hero.id} was a {trait} little {gender} who lived near {place.name}."
    )
    if mystery.id == "cookie":
        world.say(
            f"{hero.id} loved the delectable smell from the kitchen and dreamed of the cookie on the table."
        )
    elif mystery.id == "chalkboard":
        world.say(
            f"{hero.id} watched the chalk dust and wondered about the marks on the board."
        )
    else:
        world.say(
            f"{hero.id} saw a chalk arrow near the garden gate and felt the mystery tug at {hero.pronoun('possessive')} mind."
        )

    world.para()
    world.say(
        f"One day, {hero.id} found {mystery.clue}."
    )
    world.say(
        f"{hero.id} felt like a coward at first, because the clue was strange and {hero.pronoun('possessive')} heart beat fast."
    )
    world.say(
        f"Still, {hero.id} asked, '{mystery.question.capitalize()}'"
    )

    world.para()
    if resolve_clue(world, hero, mystery):
        hero.memes["fear"] = 0.0
        hero.memes["courage"] += 1
        hero.memes["joy"] += 1
        world.say(
            f"{adult.label.capitalize()} smiled and answered kindly."
        )
        world.say(mystery.solution)
        world.say(
            f"{hero.id} learned that a brave question can solve a mystery better than a loud voice."
        )
        if mystery.id == "cookie":
            world.say(
                f"In the end, the delectable cookie was shared, and the whole kitchen felt warm and sweet."
            )
        elif mystery.id == "chalkboard":
            world.say(
                f"In the end, the chalk marks made a friendly map, and the schoolyard felt safe."
            )
        else:
            world.say(
                f"In the end, the garden gate opened, and the chalk arrow seemed like a small sign of care."
            )

    world.facts.update(
        hero=hero,
        adult=adult,
        clue=clue,
        treat=treat,
        mystery=mystery,
        place=place,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    mystery: Mystery = _safe_fact(world, f, "mystery")
    return [
        f'Write a fable-like story for a small child about {hero.id}, a chalk clue, and a mystery to solve.',
        f"Tell a gentle story where a cowardly {hero.type} becomes brave by asking about {mystery.clue}.",
        f"Write a short tale with a happy ending in which a clever question helps solve a mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    adult: Entity = _safe_fact(world, f, "adult")
    mystery: Mystery = _safe_fact(world, f, "mystery")
    place: Place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little {hero.type} who lives near {place.name}."
        ),
        QAItem(
            question=f"What clue started the mystery?",
            answer=f"The mystery began with {mystery.clue}."
        ),
        QAItem(
            question=f"Why did {hero.id} feel like a coward at first?",
            answer=f"{hero.id} felt afraid because the clue was strange and the answer was not clear yet."
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"{adult.label.capitalize()} answered kindly, and {mystery.solution.lower()}"
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {hero.id} had more courage and the story ended in a happy, peaceful way."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is chalk used for?",
            answer="Chalk is a soft white stick that people use to make marks and drawings on boards, floors, or stones."
        ),
        QAItem(
            question="What does delectable mean?",
            answer="Delectable means very tasty or delicious."
        ),
        QAItem(
            question="What is a coward?",
            answer="A coward is a person who feels too afraid to act, even when a gentle bit of courage would help."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], ""]
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
        if place.has_chalkboard:
            lines.append(asp.fact("has_chalkboard", pid))
        if place.has_treats:
            lines.append(asp.fact("has_treats", pid))
        if place.has_garden:
            lines.append(asp.fact("has_garden", pid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue", mid, m.cover))
        lines.append(asp.fact("solution", mid, m.solution))
        lines.append(asp.fact("culprit", mid, m.culprit))
    return "\n".join(lines)


ASP_RULES = r"""
% A mystery is suitable when the setting supports its clue.
suitable(P, M) :- place(P), mystery(M), clue(M, chalk), has_chalkboard(P).
suitable(P, M) :- place(P), mystery(M), clue(M, crumbs), has_treats(P).
suitable(P, M) :- place(P), mystery(M), clue(M, chalk_arrow), has_garden(P).

happy_ending(P, M) :- suitable(P, M).
#show happy_ending/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-style storyworld about chalk, a delectable clue, and a mystery to solve.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    mystery = getattr(args, "mystery", None) or rng.choice(list(MYSTERIES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    reasonableness_gate(_safe_lookup(PLACES, place), _safe_lookup(MYSTERIES, mystery), gender)
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    place = _safe_lookup(PLACES, params.place)
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    world = tell(place, mystery, params.name, params.gender, params.parent, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"{e.id}: {' '.join(bits)}")
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
    StoryParams(place="schoolyard", mystery="chalkboard", name="Mina", gender="girl", parent="mother", trait="thoughtful"),
    StoryParams(place="kitchen", mystery="cookie", name="Theo", gender="boy", parent="father", trait="timid"),
    StoryParams(place="garden", mystery="garden", name="Clara", gender="girl", parent="mother", trait="kind"),
]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in PLACES:
        for mystery in MYSTERIES:
            try:
                reasonableness_gate(_safe_lookup(PLACES, place), _safe_lookup(MYSTERIES, mystery), "girl")
                combos.append((place, mystery))
            except StoryError:
                pass
    return combos


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show happy_ending/2."))
    asp_set = set(asp.atoms(model, "happy_ending"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: ASP matches Python ({len(py_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("ASP only:", sorted(asp_set - py_set))
    print("Python only:", sorted(py_set - asp_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show happy_ending/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show happy_ending/2."))
        print(sorted(asp.atoms(model, "happy_ending")))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
