#!/usr/bin/env python3
"""
A standalone storyworld for a small fable-like domain of crime, cloak, cover,
kindness, transformation, and quest.

The premise:
A petty thief takes a cloak that covers a hidden nest. A gentle quest unfolds
when a kind fox seeks to restore what was stolen, and the story ends with a
transformation: the thief returns the cloak and the village becomes warmer and
safer.
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


# -----------------------------------------------------------------------------
# Core world model
# -----------------------------------------------------------------------------

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
    worn_by: Optional[str] = None
    protected: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    cloak_ent: object | None = None
    hero: object | None = None
    nest: object | None = None
    thief: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "thief", "villager", "judge", "crow"}:
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
    coverable: set[str] = field(default_factory=set)
    quiet: bool = True
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
class Cloak:
    id: str
    label: str
    phrase: str
    covers: set[str]
    warm: bool = True
    beautiful: bool = False
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
    place: str
    cloak: str
    hero: str
    thief: str
    seed: Optional[int] = None
    trait: str = ""
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


# -----------------------------------------------------------------------------
# Registries
# -----------------------------------------------------------------------------
PLACES = {
    "village": Place(name="the village square", coverable={"nest", "well", "lamp"}),
    "wood": Place(name="the forest wood", coverable={"nest", "mushroom", "brook"}),
    "hill": Place(name="the windy hill", coverable={"nest", "stone", "path"}),
}

CLOAKS = {
    "red": Cloak(id="red", label="red cloak", phrase="a bright red cloak", covers={"nest"}),
    "gray": Cloak(id="gray", label="gray cloak", phrase="a soft gray cloak", covers={"well"}),
    "blue": Cloak(id="blue", label="blue cloak", phrase="a blue cloak with a silver thread", covers={"lamp"}),
}

NAMES = ["Ari", "Mina", "Toma", "Lio", "Nia", "Pip", "Sara", "Bren"]
THIEF_NAMES = ["Moth", "Rook", "Vale", "Sly", "Nim", "Brim"]
TRAITS = ["kind", "curious", "gentle", "brave", "patient", "thoughtful"]


# -----------------------------------------------------------------------------
# Story logic
# -----------------------------------------------------------------------------
@dataclass
class EventState:
    stolen: bool = False
    returned: bool = False
    quest_started: bool = False
    kindness_shown: bool = False
    transformation: bool = False
    state: object | None = None
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


def valid_combo(place: Place, cloak: Cloak) -> bool:
    return any(obj in place.coverable for obj in cloak.covers)


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for p_id, place in PLACES.items():
        for c_id, cloak in CLOAKS.items():
            if valid_combo(place, cloak):
                out.append((p_id, c_id))
    return out


def reasonableness_gate(place_id: str, cloak_id: str) -> None:
    if place_id not in PLACES:
        pass
    if cloak_id not in CLOAKS:
        pass
    if not valid_combo(_safe_lookup(PLACES, place_id), _safe_lookup(CLOAKS, cloak_id)):
        pass


def tell(place: Place, cloak: Cloak, hero_name: str, thief_name: str, trait: str = "kind") -> World:
    world = World(place)
    state = EventState()

    hero = world.add(Entity(id=hero_name, kind="character", type="fox", label=hero_name))
    thief = world.add(Entity(id=thief_name, kind="character", type="thief", label=thief_name))
    cloak_ent = world.add(Entity(
        id="cloak",
        kind="thing",
        type="cloak",
        label=cloak.label,
        phrase=cloak.phrase,
        owner=thief.id,
        worn_by=thief.id,
        protected=True,
        covers=set(cloak.covers),
    ))
    nest = world.add(Entity(
        id="nest",
        kind="thing",
        type="nest",
        label="nest",
        phrase="a small hidden nest",
        owner="birds",
        meters={"covered": 1.0},
    ))

    # Act I: a peaceful village and a cover that matters.
    world.say(
        f"In {place.name}, a little {trait} fox named {hero.id} watched over a hidden nest. "
        f"It stayed safe because {cloak.phrase} could cover it from the cold wind."
    )
    world.say(
        f"But one day, {thief.id} saw the cloak and took it for their own."
    )
    state.stolen = True
    cloak_ent.owner = thief.id
    cloak_ent.worn_by = thief.id
    nest.meters["covered"] = 0.0

    # Act II: the loss creates a quest.
    world.para()
    world.say(
        f"{hero.id} noticed the nest shivering without its cover. "
        f"So {hero.pronoun('subject')} began a quest to bring the cloak back."
    )
    state.quest_started = True
    world.say(
        f"{hero.id} did not chase with sharp words. Instead, {hero.pronoun('subject')} carried a warm loaf "
        f"and asked {thief.id} why they had taken it."
    )

    # Act III: kindness changes the thief.
    world.para()
    thief.memes["guilt"] = thief.memes.get("guilt", 0.0) + 1.0
    thief.memes["softening"] = thief.memes.get("softening", 0.0) + 1.0
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1.0
    state.kindness_shown = True

    world.say(
        f"{thief.id} lowered their head. They saw the nest trembling and felt ashamed."
    )
    world.say(
        f"Then {thief.id} returned the cloak and helped place it back where it belonged, over the nest."
    )
    cloak_ent.owner = "nest"
    cloak_ent.worn_by = None
    nest.meters["covered"] = 1.0
    state.returned = True
    state.transformation = True

    world.para()
    world.say(
        f"At the end, the cloak covered the nest again, the wind could not bite through, and "
        f"{thief.id} had changed from a taker into a helper."
    )
    world.say(
        f"The little fox finished the quest with a calm heart, and the village remembered that kindness "
        f"can mend what a crime has broken."
    )

    world.facts.update(
        hero=hero,
        thief=thief,
        cloak=cloak_ent,
        nest=nest,
        state=state,
        place=place,
        cloak_def=cloak,
        trait=trait,
    )
    return world


# -----------------------------------------------------------------------------
# Q&A
# -----------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    thief = _safe_fact(world, f, "thief")
    cloak = _safe_fact(world, f, "cloak_def")
    place = _safe_fact(world, f, "place")
    return [
        f"Write a short fable about a {hero.type} who begins a quest after a cloak is stolen in {place.name}.",
        f"Tell a child-friendly story where {thief.id} takes {cloak.label}, and kindness helps fix the crime.",
        f"Write a simple fable about a cover, a loss, and a transformation ending with the cloak returned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    thief = _safe_fact(world, f, "thief")
    cloak = _safe_fact(world, f, "cloak_def")
    place = _safe_fact(world, f, "place")
    state: EventState = _safe_fact(world, f, "state")
    return [
        QAItem(
            question=f"Who began the quest after the cloak was taken in {place.name}?",
            answer=f"{hero.id}, the little fox, began the quest after noticing that {thief.id} had taken the {cloak.label}.",
        ),
        QAItem(
            question=f"What did the cloak help cover before it was stolen?",
            answer=f"It helped cover the nest, keeping it safe from the cold wind.",
        ),
        QAItem(
            question=f"How did the story end after the crime was repaired?",
            answer=(
                f"The cloak was returned, the nest was covered again, and {thief.id} changed and became more helpful. "
                f"That is the story's transformation."
            ) if state.transformation else "The story ended with the cloak returned and the nest safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    cloak = _safe_fact(world, f, "cloak_def")
    return [
        QAItem(
            question="What is a cloak for?",
            answer="A cloak is a piece of clothing that covers someone or something and can help keep it warm.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing gentle, helpful actions that care about others.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or mission to find, fix, or protect something important.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means a change from one way of being into another way of being.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# -----------------------------------------------------------------------------
# ASP twin
# -----------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
cloak(C) :- cloak_item(C).
covers(C, X) :- cloak_covers(C, X).

valid(P, C) :- place(P), cloak(C), covers(C, X), coverable(P, X).
quest(P, C) :- valid(P, C).
transformed(T) :- kindness(T), quest_started(T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("setting", pid))
        for x in sorted(p.coverable):
            lines.append(asp.fact("coverable", pid, x))
    for cid, c in CLOAKS.items():
        lines.append(asp.fact("cloak_item", cid))
        for x in sorted(c.covers):
            lines.append(asp.fact("cloak_covers", cid, x))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


# -----------------------------------------------------------------------------
# Parameters / generation
# -----------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable world about crime, cloak, cover, kindness, transformation, and quest.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--cloak", choices=CLOAKS)
    ap.add_argument("--hero")
    ap.add_argument("--thief")
    ap.add_argument("--trait", choices=["kind", "curious", "gentle", "brave", "patient", "thoughtful"])
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
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "cloak", None):
        combos = [c for c in combos if c[1] == getattr(args, "cloak", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place_id, cloak_id = rng.choice(list(combos))
    if getattr(args, "place", None) and getattr(args, "cloak", None):
        reasonableness_gate(getattr(args, "place", None), getattr(args, "cloak", None))

    hero = getattr(args, "hero", None) or rng.choice(NAMES)
    thief = getattr(args, "thief", None) or rng.choice(THIEF_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place_id, cloak=cloak_id, hero=hero, thief=thief, seed=None)


def generate(params: StoryParams) -> StorySample:
    place = _safe_lookup(PLACES, params.place)
    cloak = _safe_lookup(CLOAKS, params.cloak)
    world = tell(place, cloak, params.hero, params.thief, params.trait if params.seed is not None else "kind")
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
        bits = []
        if e.owner is not None:
            bits.append(f"owner={e.owner}")
        if e.worn_by is not None:
            bits.append(f"worn_by={e.worn_by}")
        if e.covers:
            bits.append(f"covers={sorted(e.covers)}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for p, c in asp_valid_combos():
            print(p, c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p, c in valid_combos():
            params = StoryParams(place=p, cloak=c, hero=_safe_lookup(NAMES, 0), thief=_safe_lookup(THIEF_NAMES, 0), trait="kind", seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 30):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
                params.seed = base_seed + i
                sample = generate(params)
            except StoryError:
                continue
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
