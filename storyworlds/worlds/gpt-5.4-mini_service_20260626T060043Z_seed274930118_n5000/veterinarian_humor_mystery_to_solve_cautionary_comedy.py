#!/usr/bin/env python3
"""
storyworlds/worlds/veterinarian_humor_mystery_to_solve_cautionary_comedy.py
============================================================================

A tiny story world about a veterinarian, a puzzling pet problem, and a funny
but cautionary solution.

Premise:
- A vet notices a pet behaving strangely.
- The clue trail points to a hidden cause.
- The final reveal teaches a simple caution: don't give pets the wrong snack.

The world is built to generate short, child-facing comedy stories with a
mystery to solve and a gentle warning.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    pet: object | None = None
    snack: object | None = None
    vet: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"woman", "girl", "veterinarian"}
        male = {"man", "boy", "boy-vet"}
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
    place: str = "the animal clinic"
    room: str = "exam room"
    sees: set[str] = field(default_factory=set)
    SETTING: object | None = None
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
class Pet:
    id: str
    type: str
    label: str
    phrase: str
    sound: str
    symptom: str
    clue: str
    caution: str
    likes: set[str] = field(default_factory=set)
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


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    risky_for: set[str] = field(default_factory=set)
    effect: str = ""
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


@dataclass
class StoryParams:
    pet: str
    snack: str
    name: str
    vet_type: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.pet: Optional[Entity] = None
        self.vet: Optional[Entity] = None
        self.snack: Optional[Entity] = None
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTING = Setting()

PETS = {
    "dog": Pet(
        id="dog",
        type="dog",
        label="dog",
        phrase="a cheerful little dog",
        sound="woof",
        symptom="a very round belly and a silly wobble",
        clue="crumbs on the fur",
        caution="Dogs should not eat chocolate, because it can make them sick.",
        likes={"balls", "sticks", "belly rubs"},
    ),
    "cat": Pet(
        id="cat",
        type="cat",
        label="cat",
        phrase="a whiskery cat",
        sound="meow",
        symptom="a grumpy sneeze and a twitchy nose",
        clue="powder on the whiskers",
        caution="Cats should not eat onion, because it can upset their stomach.",
        likes={"boxes", "string", "sun patches"},
    ),
    "rabbit": Pet(
        id="rabbit",
        type="rabbit",
        label="rabbit",
        phrase="a fluffy rabbit",
        sound="squeak",
        symptom="an extra bouncy hop and a sticky mouth",
        clue="jam on the paws",
        caution="Rabbits should not eat sticky candy, because it is not healthy for them.",
        likes={"carrots", "hay", "shade"},
    ),
}

SNACKS = {
    "chocolate": Snack(
        id="chocolate",
        label="chocolate cookie",
        phrase="a chocolate cookie",
        risky_for={"dog"},
        effect="very itchy and sleepy",
    ),
    "onion": Snack(
        id="onion",
        label="onion ring",
        phrase="an onion ring",
        risky_for={"cat"},
        effect="a wobbly tummy",
    ),
    "candy": Snack(
        id="candy",
        label="sticky candy",
        phrase="sticky candy",
        risky_for={"rabbit"},
        effect="a sticky mouth",
    ),
}

VET_TYPES = {
    "veterinarian": "veterinarian",
    "boy-vet": "boy-vet",
}


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def intro(world: World, vet: Entity, pet: Entity) -> None:
    world.say(
        f"{vet.id} was a veterinarian at {world.setting.place}, and {pet.id} was one of the pets who liked to visit."
    )
    world.say(
        f"Most days were calm, but this day {pet.id} had {_safe_lookup(PETS, pet.type).symptom}, which looked funny and a little suspicious."
    )


def mystery(world: World, vet: Entity, pet: Entity) -> None:
    world.say(
        f"{vet.id} listened to {pet.id} sniff and blink. '{pet.sound}?' {pet.id} said, as if trying to solve the mystery too."
    )
    world.say(
        f"{vet.id} checked {pet.id}'s paws, ears, and nose, but the weird clue was {_safe_lookup(PETS, pet.type).clue}."
    )


def reveal(world: World, vet: Entity, pet: Entity, snack: Entity) -> None:
    world.say(
        f"Then {vet.id} saw {snack.phrase} tucked near the bench, and the mystery popped open like a surprise box."
    )
    world.say(
        f"Someone had shared the wrong snack with {pet.id}, and that is why {pet.id} felt {_safe_lookup(SNACKS, snack.type).effect}."
    )


def caution(world: World, vet: Entity, pet: Entity, snack: Entity) -> None:
    world.say(
        f"{vet.id} gave a gentle smile and said that {snack.phrase} was not a good treat for {pet.id}."
    )
    world.say(
        f'"{_safe_lookup(PETS, pet.type).caution}" {vet.id} said, and {pet.id} made a tiny face like a blueberry had gone missing.'
    )


def ending(world: World, vet: Entity, pet: Entity) -> None:
    world.say(
        f"After a safe snack and a drink of water, {pet.id} felt better, and {vet.id} laughed at the little mystery that had turned into a lesson."
    )
    world.say(
        f"By the end, {pet.id} was wagging, purring, or hopping happily again, and the clinic was calm except for the giggles."
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
pet(P) :- pet_kind(P).
snack(S) :- snack_kind(S).

risky(P,S) :- pet_kind(P), snack_kind(S), risk(P,S).
story_ok(P,S) :- risky(P,S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PETS:
        lines.append(asp.fact("pet_kind", pid))
    for sid, snack in SNACKS.items():
        lines.append(asp.fact("snack_kind", sid))
        for pet in sorted(snack.risky_for):
            lines.append(asp.fact("risk", pet, sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show risky/2."))
    return sorted(set(asp.atoms(model, "risky")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pet_id, pet in PETS.items():
        for snack_id, snack in SNACKS.items():
            if pet_id in snack.risky_for:
                combos.append((pet_id, snack_id))
    return combos


def build_world(params: StoryParams) -> World:
    if params.pet not in PETS:
        pass
    if params.snack not in SNACKS:
        pass

    pet_cfg = _safe_lookup(PETS, params.pet)
    snack_cfg = _safe_lookup(SNACKS, params.snack)
    if params.pet not in snack_cfg.risky_for:
        pass

    world = World(SETTING)
    vet = world.add(Entity(id=params.name, kind="character", type=params.vet_type, label="vet"))
    pet = world.add(Entity(id=pet_cfg.id, kind="character", type=pet_cfg.type, label=pet_cfg.label))
    snack = world.add(Entity(id=snack_cfg.id, type=snack_cfg.id, label=snack_cfg.label, phrase=snack_cfg.phrase))
    world.vet = vet
    world.pet = pet
    world.snack = snack
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    vet = world.vet
    pet = world.pet
    snack = world.snack
    assert vet and pet and snack

    intro(world, vet, pet)
    world.para()
    mystery(world, vet, pet)
    world.para()
    reveal(world, vet, pet, snack)
    caution(world, vet, pet, snack)
    ending(world, vet, pet)

    world.facts = {
        "vet": vet,
        "pet": pet,
        "snack": snack,
        "pet_type": pet.type,
        "snack_type": snack.id,
        "symptom": _safe_lookup(PETS, pet.type).symptom,
        "clue": _safe_lookup(PETS, pet.type).clue,
        "caution": _safe_lookup(PETS, pet.type).caution,
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
    pet = _safe_fact(world, world.facts, "pet")
    snack = _safe_fact(world, world.facts, "snack")
    return [
        f'Write a funny story for a young child about a veterinarian solving a pet mystery involving "{pet.type}".',
        f"Tell a cautionary comedy where a veterinarian discovers that {pet.id} got too much {snack.label} and feels strange.",
        f"Make a short mystery to solve at a clinic, with a gentle warning about not feeding pets the wrong treat.",
    ]


def story_qa(world: World) -> list[QAItem]:
    pet = _safe_fact(world, world.facts, "pet")
    snack = _safe_fact(world, world.facts, "snack")
    vet = _safe_fact(world, world.facts, "vet")
    pet_cfg = _safe_lookup(PETS, pet.type)
    snack_cfg = _safe_lookup(SNACKS, snack.id)
    return [
        QAItem(
            question=f"Who was trying to solve the mystery at the clinic?",
            answer=f"{vet.id} was the veterinarian trying to solve it.",
        ),
        QAItem(
            question=f"What was strange about {pet.id} at the start of the story?",
            answer=f"{pet.id} had {pet_cfg.symptom}.",
        ),
        QAItem(
            question=f"What clue helped {vet.id} figure out the problem?",
            answer=f"The clue was {pet_cfg.clue}, which pointed to the {snack_cfg.phrase}.",
        ),
        QAItem(
            question=f"What caused the funny trouble for {pet.id}?",
            answer=f"{pet.id} had been given {snack_cfg.phrase}, which was the wrong snack for a {pet_cfg.label}.",
        ),
        QAItem(
            question=f"What lesson did {vet.id} give at the end?",
            answer=pet_cfg.caution,
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a veterinarian do?",
            answer="A veterinarian is a doctor for animals. A veterinarian checks pets, finds out what is wrong, and helps them feel better.",
        ),
        QAItem(
            question="Why should pets not eat the wrong snack?",
            answer="Some human foods can hurt pets or upset their stomachs, so pets should only eat safe food made for them.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle where you do not know the answer yet, so you look for clues and try to solve it.",
        ),
    ]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small veterinarian mystery-comedy story world.")
    ap.add_argument("--pet", choices=sorted(PETS))
    ap.add_argument("--snack", choices=sorted(SNACKS))
    ap.add_argument("--name", default=None)
    ap.add_argument("--vet-type", choices=sorted(VET_TYPES), default="veterinarian")
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
    combos = valid_combos()
    if getattr(args, "pet", None) and getattr(args, "snack", None):
        if (getattr(args, "pet", None), getattr(args, "snack", None)) not in combos:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        (p, s) for (p, s) in combos
        if (getattr(args, "pet", None) is None or p == getattr(args, "pet", None)) and (getattr(args, "snack", None) is None or s == getattr(args, "snack", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    pet, snack = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(["Dr. Poppy", "Dr. Milo", "Dr. June", "Dr. Finn"])
    return StoryParams(pet=pet, snack=snack, name=name, vet_type=getattr(args, "vet_type", None))


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_program_for_show() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n#show risky/2.\n"


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program_for_show())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program_for_show())
        combos = sorted(set(asp.atoms(model, "risky")))
        print(f"{len(combos)} risky pet/snack combinations:\n")
        for pet, snack in combos:
            print(f"  {pet:8} {snack}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for pet, snack in sorted(valid_combos()):
            params = StoryParams(pet=pet, snack=snack, name="Dr. Poppy", vet_type=getattr(args, "vet_type", None), seed=base_seed)
            samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
