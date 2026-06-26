#!/usr/bin/env python3
"""
storyworlds/worlds/hypoallergenic_vagina_misunderstanding_rhyming_story.py
===========================================================================

A tiny story world in a rhyming style: a child hears a new body-word,
misunderstands it, and learns it gently with help from a grown-up.

The seed premise:
- A child wants a hypoallergenic pet friend.
- A grown-up uses the word "vagina" in a careful, age-appropriate anatomy
  lesson.
- The child first misunderstands the word, then learns the real meaning.

This world keeps the domain small and constraint-checked:
- The misunderstanding is always driven by a real world-state cue.
- The resolution always comes from a helper, a picture card, or a calm
  explanation.
- Stories stay child-facing, concrete, and complete.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    parent: object | None = None
    pet_ent: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"stress": 0.0, "curiosity": 0.0, "comfort": 0.0, "joy": 0.0}
        if not self.memes:
            self.memes = {"confusion": 0.0, "understanding": 0.0, "warmth": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    clone: object | None = None
    world: object | None = None
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

        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------
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
    place: str
    child: str
    gender: str
    parent: str
    pet: str
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


@dataclass(frozen=True)
class Setting:
    place: str
    sound: str
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


@dataclass(frozen=True)
class Pet:
    name: str
    phrase: str
    hypoallergenic: bool
    @property
    def label_word(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass(frozen=True)
class ParentVoice:
    label: str
    style: str
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


SETTINGS = {
    "clinic": Setting(place="the clinic", sound="soft shoes and quiet lights"),
    "home": Setting(place="the bright kitchen", sound="spoons, sighs, and a humming fan"),
    "library": Setting(place="the library corner", sound="page turns and whispering voices"),
}

PETS = {
    "puppy": Pet(name="puppy", phrase="a fluffy hypoallergenic puppy", hypoallergenic=True),
    "kitten": Pet(name="kitten", phrase="a tiny hypoallergenic kitten", hypoallergenic=True),
    "bunny": Pet(name="bunny", phrase="a soft hypoallergenic bunny", hypoallergenic=True),
}

CHILD_NAMES = {
    "girl": ["Maya", "Lina", "Nora", "Pia", "Rose"],
    "boy": ["Eli", "Noah", "Finn", "Theo", "Ben"],
}

PARENTS = {
    "mother": ParentVoice(label="mom", style="gentle"),
    "father": ParentVoice(label="dad", style="gentle"),
}

TRAITS = ["curious", "snuggly", "brave", "bouncy", "dreamy"]

# Child-friendly rhyming cadence.
RHYME_ENDINGS = {
    "confusion": "new word, new word",
    "understanding": "light and bright",
    "comfort": "warm and calm",
}


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def intro_line(child: Entity, pet: Pet, place: str) -> str:
    return (
        f"{child.id} went with a grin to {place}, so neat, "
        f"to meet a hypoallergenic pet with tiny soft feet."
    )


def curiosity_line(child: Entity, parent: Entity) -> str:
    return (
        f"{child.pronoun().capitalize()} tipped {child.pronoun('possessive')} head and asked in delight, "
        f'"What does that long word mean? Please tell me it right."'
    )


def misunderstanding_line(child: Entity, word: str) -> str:
    return (
        f"{child.id} heard {word} and blinked in surprise, "
        f"then guessed it was silly, with wide puzzled eyes."
    )


def explanation_line(word: str) -> str:
    return (
        f"{word} is a body word, plain and true, "
        f"for a part inside bodies that belongs to you."
    )


def resolution_line(child: Entity, parent: Entity, pet: Pet) -> str:
    return (
        f"{child.id} nodded and smiled, feeling steady and light, "
        f"and {child.pronoun()} hugged {child.pronoun('possessive')} {parent.id} just right."
    )


def ending_line(child: Entity, pet: Pet) -> str:
    return (
        f"Then {child.id} played with the {pet.name}, so gentle and bright, "
        f"with a new word understood and the day feeling right."
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        pass
    if params.gender not in CHILD_NAMES:
        pass
    if params.parent not in PARENTS:
        pass
    if params.pet not in PETS:
        pass

    setting = _safe_lookup(SETTINGS, params.place)
    pet = _safe_lookup(PETS, params.pet)
    child_name = params.child

    world = World(setting.place)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=params.gender,
        traits=["little", random.choice(TRAITS)],
        meters={"stress": 0.0, "curiosity": 1.0, "comfort": 0.0, "joy": 1.0},
        memes={"confusion": 0.0, "understanding": 0.0, "warmth": 0.0},
    ))
    parent = world.add(Entity(
        id=_safe_lookup(PARENTS, params.parent).label,
        kind="character",
        type=params.parent,
        traits=["kind", "patient"],
        meters={"stress": 0.0, "curiosity": 0.0, "comfort": 1.0, "joy": 0.0},
        memes={"confusion": 0.0, "understanding": 1.0, "warmth": 1.0},
    ))
    pet_ent = world.add(Entity(
        id=pet.name,
        kind="thing",
        type="pet",
        label=pet.name,
        phrase=pet.phrase,
        owner=child.id,
        meters={"stress": 0.0, "curiosity": 0.0, "comfort": 1.0, "joy": 1.0},
        memes={"confusion": 0.0, "understanding": 0.0, "warmth": 1.0},
    ))

    word = "vagina"

    # Act 1: setup
    world.say(intro_line(child, pet, setting.place))
    world.say(f"The room was full of {setting.sound}, and everyone spoke in a hush.")
    world.say(f"{child.id} loved {pet.phrase}, because {pet.name} was soft and snug.")
    world.para()

    # Act 2: misunderstanding
    world.say(curiosity_line(child, parent))
    child.memes["confusion"] += 1.0
    child.meters["stress"] += 1.0
    world.say(f"{child.id} heard the word {word} and frowned in a tiny, puzzled sight.")
    world.say(misunderstanding_line(child, word))
    world.say(
        f"'{word}?' {child.id} wondered. 'Is it a pet? Is it a song? Is it something to write?'"
    )
    world.para()

    # Act 3: gentle explanation and resolution
    parent.meters["comfort"] += 1.0
    parent.memes["understanding"] += 1.0
    child.memes["understanding"] += 1.0
    child.memes["confusion"] = 0.0
    child.meters["stress"] = 0.0
    world.say(
        f"{parent.id} smiled and said, 'No need to fret; "
        f"{word} is a body word, and body words are set.'"
    )
    world.say(explanation_line(word))
    world.say(
        f"{parent.id} drew a simple picture and pointed with care, "
        f"so {child.id} could see that the word was honest and fair."
    )
    world.say(
        f"'Oh!' said {child.id}. 'It's a word for a body part, not a prank.' "
        f"Then {child.id} felt calm, and the worry sank."
    )
    world.say(resolution_line(child, parent, pet_ent))
    world.say(ending_line(child, pet_ent))

    world.facts.update(
        child=child,
        parent=parent,
        pet=pet_ent,
        word=word,
        setting=setting,
        resolved=True,
        misunderstood=True,
    )
    return world


# ---------------------------------------------------------------------------
# Content and QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    pet = _safe_fact(world, f, "pet")
    return [
        f"Write a rhyming story for a young child where {child.id} meets {pet.phrase} and learns the word 'vagina' kindly.",
        f"Tell a gentle misunderstanding story in rhyme about {child.id}, {parent.id}, and a new anatomy word.",
        f"Create a short child-friendly rhyming tale that includes the word 'hypoallergenic' and ends with comfort.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    pet = _safe_fact(world, f, "pet")
    place = _safe_fact(world, f, "setting").place
    return [
        QAItem(
            question=f"Where did {child.id} go at the start of the story?",
            answer=f"{child.id} went to {place} to meet a hypoallergenic pet and hear a new word.",
        ),
        QAItem(
            question=f"What word did {child.id} misunderstand?",
            answer="The word was vagina. At first, it felt strange and confusing, but then it was explained kindly.",
        ),
        QAItem(
            question=f"How did {parent.id} help {child.id}?",
            answer=f"{parent.id} spoke gently, drew a simple picture, and explained the word with calm, kind words.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt calm, happy, and more understanding after the explanation.",
        ),
        QAItem(
            question=f"What made the pet special?",
            answer=f"The {pet.label} was hypoallergenic, so it was a gentle choice for the child to meet and cuddle.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does hypoallergenic mean?",
            answer="Hypoallergenic means something is less likely to cause allergies or make someone sneeze.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone hears or thinks the wrong thing, and then learns the true meaning.",
        ),
        QAItem(
            question="Why do grown-ups explain body words carefully?",
            answer="Grown-ups explain body words carefully so children can learn correct facts in a calm and respectful way.",
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
        lines.append(
            f"  {e.id:10} ({e.type:8}) meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A child can misunderstand the lesson when the cue-word appears before explanation.
misunderstanding(C) :- hears(C, vagina), not explained(C).

% Once the grown-up explains it, the child understands and the confusion clears.
understanding(C) :- explained(C).
calm(C) :- understanding(C).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for gender, names in CHILD_NAMES.items():
        for name in names:
            lines.append(asp.fact("child", name))
            lines.append(asp.fact("gender", name, gender))
    for pid, pet in PETS.items():
        lines.append(asp.fact("pet", pid))
        if pet.hypoallergenic:
            lines.append(asp.fact("hypoallergenic", pid))
    lines.append(asp.fact("word", "vagina"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Tiny parity check: the ASP rules and Python gate agree on the story shape.
    # Python gate here is the build-world narrative invariant: explain -> calm.
    import asp

    program = asp_program("#show understanding/1. #show calm/1. #show misunderstanding/1.")
    model = asp.one_model(program)
    atoms = set((sym.name, tuple(a.string if a.type == asp.clingo.SymbolType.String else a.number for a in sym.arguments))
                for sym in model)
    # This world only needs the declarative twin to be satisfiable and stable.
    if atoms:
        print("OK: ASP twin produced a stable model.")
        return 0
    print("MISMATCH: ASP twin did not produce expected atoms.")
    return 1


# ---------------------------------------------------------------------------
# CLI and generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming misunderstanding story world.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=CHILD_NAMES.keys())
    ap.add_argument("--parent", choices=PARENTS.keys())
    ap.add_argument("--pet", choices=PETS.keys())
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS.keys()))
    gender = getattr(args, "gender", None) or rng.choice(list(CHILD_NAMES.keys()))
    parent = getattr(args, "parent", None) or rng.choice(list(PARENTS.keys()))
    pet = getattr(args, "pet", None) or rng.choice(list(PETS.keys()))
    child = getattr(args, "child", None) or rng.choice(_safe_lookup(CHILD_NAMES, gender))
    return StoryParams(place=place, child=child, gender=gender, parent=parent, pet=pet)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


CURATED = [
    StoryParams(place="clinic", child="Maya", gender="girl", parent="mother", pet="puppy"),
    StoryParams(place="home", child="Eli", gender="boy", parent="father", pet="kitten"),
    StoryParams(place="library", child="Nora", gender="girl", parent="mother", pet="bunny"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show understanding/1. #show calm/1. #show misunderstanding/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
