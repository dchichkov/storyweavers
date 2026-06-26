#!/usr/bin/env python3
"""
A tiny mystery storyworld: a child hears a bonk, follows clues, and solves the
problem with a calm, clever fix.

Seed premise:
- A child with an afro hears a suspicious bonk.
- Something is missing, bent, or out of place.
- The child investigates, compares clues, and finds the real cause.
- The ending proves the mystery was solved and the afro was safe.

This script is standalone and follows the Storyweavers world contract.
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

    region: object | None = None
    hero: object | None = None
    parent: object | None = None
    prop: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    indoor: bool
    clues: list[str] = field(default_factory=list)
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
    noun: str
    verb: str
    sound: str
    clue: str
    solution: str
    risk: str
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
class Prop:
    id: str
    label: str
    phrase: str
    region: str
    protective: bool = False
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
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.trace = list(self.trace)
        clone.facts = dict(self.facts)
        return clone


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    if not hero:
        return out
    if hero.memes.get("worry", 0) >= THRESHOLD and ("worry", hero.id) not in world.fired:
        world.fired.add(("worry", hero.id))
        out.append(f"{hero.id} felt a little worried, but kept looking for clues.")
    return out


def _r_solved(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    culprit = world.facts.get("culprit")
    mystery = world.facts.get("mystery")
    if not hero or not culprit or not mystery:
        return out
    if hero.memes.get("certainty", 0) >= THRESHOLD and ("solved", mystery.id) not in world.fired:
        world.fired.add(("solved", mystery.id))
        out.append("The clue fit the story.")
    return out


CAUSAL_RULES = [
    _r_worry,
    _r_solved,
]


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.trace)
            out = rule(world)
            if out:
                changed = True
                for s in out:
                    world.say(s)
            if len(world.trace) != before:
                pass


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for c in s.clues:
            lines.append(asp.fact("clue", sid, c))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("sound", mid, m.sound))
        lines.append(asp.fact("risk", mid, m.risk))
        for t in sorted(m.tags):
            lines.append(asp.fact("tagged", mid, t))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        lines.append(asp.fact("region", pid, p.region))
        if p.protective:
            lines.append(asp.fact("protective", pid))
    return "\n".join(lines)


ASP_RULES = r"""
same_case(M) :- mystery(M).
mystery_solved(M) :- mystery(M), sound(M, bonk), risk(M, afro), tagged(M, clue).
compatible_prop(P, M) :- protective(P), mystery(M), region(P, head).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mystery_solved/1."))
    asp_set = set(asp.atoms(model, "mystery_solved"))
    py_set = set()
    for mid, m in MYSTERIES.items():
        if m.sound == "bonk" and m.risk == "afro":
            py_set.add((mid,))
    if asp_set == py_set:
        print(f"OK: clingo gate matches python gate ({len(py_set)} mysteries).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  clingo:", sorted(asp_set))
    print("  python:", sorted(py_set))
    return 1


SETTINGS = {
    "hall": Setting(place="the hall", indoor=True, clues=["footprints", "echo", "glint"]),
    "library": Setting(place="the library", indoor=True, clues=["bookmark", "ladder", "whisper"]),
    "garden": Setting(place="the garden", indoor=False, clues=["mud", "leaf", "path"]),
}

MYSTERIES = {
    "bonk_afro": Mystery(
        id="bonk_afro",
        noun="afro",
        verb="bonk",
        sound="bonk",
        clue="soft cap",
        solution="a book fell from a shelf and tapped the chair",
        risk="afro",
        tags={"clue", "book", "chair"},
    ),
    "bonk_box": Mystery(
        id="bonk_box",
        noun="box",
        verb="bonk",
        sound="bonk",
        clue="wobbly stack",
        solution="a box tipped over in the hall",
        risk="box",
        tags={"clue", "box", "stack"},
    ),
    "rustle_hat": Mystery(
        id="rustle_hat",
        noun="hat",
        verb="rustle",
        sound="rustle",
        clue="paper trail",
        solution="a mouse was hiding in a paper nest",
        risk="hat",
        tags={"clue", "mouse", "paper"},
    ),
}

PROPS = {
    "mirror": Prop(id="mirror", label="small mirror", phrase="a small mirror", region="head"),
    "comb": Prop(id="comb", label="wide comb", phrase="a wide comb", region="head"),
    "lamp": Prop(id="lamp", label="desk lamp", phrase="a desk lamp", region="head", protective=False),
}

GIRL_NAMES = ["Mia", "Nora", "Ava", "Zoe", "Lily"]
BOY_NAMES = ["Leo", "Max", "Ben", "Finn", "Theo"]
TRAITS = ["curious", "careful", "brave", "gentle", "clever"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    prop: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld with bonk and afro.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    mystery = getattr(args, "mystery", None) or "bonk_afro"
    prop = getattr(args, "prop", None) or "mirror"
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, prop=prop, name=name, gender=gender, parent=parent, trait=trait)


def _story_introduce(world: World, hero: Entity, parent: Entity, mystery: Mystery) -> None:
    world.say(
        f"{hero.id} was a {hero.memes.get('trait', 'curious')} {hero.type} who liked solving little puzzles."
    )
    world.say(
        f"{hero.id}'s {parent.label_word} had given {hero.id} a neat {mystery.noun}, and {hero.id} liked how it looked."
    )


def _story_incident(world: World, hero: Entity, parent: Entity, mystery: Mystery, prop: Entity) -> None:
    hero.memes["worry"] = 1
    world.say(
        f"One day, at {world.setting.place}, there was a loud {mystery.sound} from the other room."
    )
    world.say(
        f"{hero.id} looked at the {prop.label} and wondered if the sound had touched {hero.pronoun('possessive')} {mystery.noun}."
    )


def _story_clues(world: World, hero: Entity, mystery: Mystery) -> None:
    world.say(
        f"{hero.id} noticed {world.setting.clues[0]} near the doorway, then {world.setting.clues[1]} by the chair."
    )
    world.say(
        f"That made {hero.id} think hard, because the clues did not point to a monster at all."
    )
    hero.memes["certainty"] = 1


def _story_turn(world: World, hero: Entity, parent: Entity, mystery: Mystery, prop: Entity) -> None:
    world.say(
        f"{hero.id} asked {hero.pronoun('possessive')} {parent.label_word} one careful question at a time."
    )
    world.say(
        f"At last, {hero.id} found the answer: {mystery.solution}."
    )
    world.say(
        f"The mystery was small, but the thinking was big."
    )


def _story_end(world: World, hero: Entity, parent: Entity, prop: Entity, mystery: Mystery) -> None:
    hero.memes["peace"] = 1
    world.say(
        f"{hero.id} smiled, tucked the {prop.label} away, and knew {hero.pronoun('possessive')} {mystery.noun} was safe."
    )
    world.say(
        f"{hero.id}'s {parent.label_word} laughed softly, and the room felt calm again."
    )


def generate_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    prop_cfg = _safe_lookup(PROPS, params.prop)
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={}, memes={"trait": params.trait}))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent", meters={}, memes={}))
    prop = world.add(Entity(id="prop", label=prop_cfg.label, phrase=prop_cfg.phrase, region=prop_cfg.region))
    world.facts.update(hero=hero, parent=parent, mystery=mystery, prop=prop, setting=setting)
    _story_introduce(world, hero, parent, mystery)
    world.para()
    _story_incident(world, hero, parent, mystery, prop)
    world.para()
    _story_clues(world, hero, mystery)
    _story_turn(world, hero, parent, mystery, prop)
    world.para()
    _story_end(world, hero, parent, prop, mystery)
    propagate(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    mystery: Mystery = _safe_fact(world, f, "mystery")
    return [
        f'Write a short mystery story for a child named {hero.id} that begins with a {mystery.sound} and ends with the problem solved.',
        f'Create a gentle detective tale where {hero.id} uses clues to explain what caused the bonk near the afro.',
        f'Write a child-friendly problem-solving story about an unusual sound, a careful question, and a calm solution.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    parent: Entity = _safe_fact(world, f, "parent")
    mystery: Mystery = _safe_fact(world, f, "mystery")
    return [
        QAItem(
            question=f"What sound started the mystery for {hero.id}?",
            answer=f"The mystery started with a loud {mystery.sound}.",
        ),
        QAItem(
            question=f"What did {hero.id} use to solve the problem?",
            answer=f"{hero.id} used clues, careful questions, and brave thinking to solve it.",
        ),
        QAItem(
            question=f"What was the answer to the mystery?",
            answer=f"The answer was that {mystery.solution}.",
        ),
        QAItem(
            question=f"How did {hero.id}'s {parent.label_word} feel at the end?",
            answer=f"{hero.id}'s {parent.label_word} felt calm and happy once the mystery was solved.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery story?",
            answer="A clue is a little piece of information that helps someone figure out what happened.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks carefully, asks questions, and puts clues together to solve a problem.",
        ),
        QAItem(
            question="What is an afro?",
            answer="An afro is a round, curly hairstyle that puffs out around the head.",
        ),
        QAItem(
            question="Why do people listen for sounds when solving a mystery?",
            answer="They listen for sounds because a sound can tell them where something happened or what caused the trouble.",
        ),
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hall", mystery="bonk_afro", prop="mirror", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="library", mystery="bonk_afro", prop="comb", name="Leo", gender="boy", parent="father", trait="careful"),
    StoryParams(place="garden", mystery="rustle_hat", prop="lamp", name="Ava", gender="girl", parent="mother", trait="brave"),
]


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show mystery_solved/1."))
    return sorted(set(asp.atoms(model, "mystery_solved")))


def build_story(params: StoryParams) -> StorySample:
    world = generate_world(params)
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
        print(asp_program("#show mystery_solved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show mystery_solved/1."))
        print(asp.atoms(model, "mystery_solved"))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [build_story(p) for p in CURATED]
    else:
        seen = set()
        for i in range(max(getattr(args, "n", None) * 50, 50)):
            if len(samples) >= getattr(args, "n", None):
                break
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            sample = build_story(params)
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
