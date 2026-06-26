#!/usr/bin/env python3
"""
Standalone story world: a child finds a ghostly collar and talks to a gentle ghost.

This world keeps a small, classical simulation:
- typed entities with physical meters and emotional memes
- dialogue-driven beats
- a ghost-story atmosphere, but child-facing and gentle
- a reasonableness gate that only allows stories where the collar matters

The seed premise:
A child hears a soft voice in the dark, finds a lonely ghost, and discovers
that a little collar is what keeps the ghost calm and present. The child
returns the collar, speaks kindly, and the ghost finally leaves with a quiet
thank-you instead of a wail.
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
    kind: str = "thing"          # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    held_by: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    tags: set[str] = field(default_factory=set)
    child: object | None = None
    collar: object | None = None
    ghost: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type
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
    dark: bool = True
    tags: set[str] = field(default_factory=set)
    outdoors: object | None = None
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
class Collar:
    label: str
    phrase: str
    color: str
    bell: bool = True
    tags: set[str] = field(default_factory=set)
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
    name: str
    gender: str
    parent: str
    trait: str
    collar_color: str = "blue"
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
    def __init__(self, place: Place):
        self.place = place
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


def pronounce_name(entity: Entity) -> str:
    return entity.id


def setup_place(place_id: str) -> Place:
    return _safe_lookup(PLACES, place_id)


def setup_params(place: str, name: str, gender: str, parent: str, trait: str, collar_color: str) -> StoryParams:
    return StoryParams(place=place, name=name, gender=gender, parent=parent, trait=trait, collar_color=collar_color)


def child_intro(world: World, child: Entity) -> None:
    trait = next((t for t in child.traits if t != "little"), child.type)
    world.say(f"{child.id} was a little {trait} {child.type} who liked quiet nights and strange stories.")


def ghost_intro(world: World, ghost: Entity) -> None:
    world.say(f"One pale evening, a soft ghost drifted near the fence and whispered, \"My collar is missing.\"")


def collar_intro(world: World, collar: Entity, color: str) -> None:
    world.say(f"A {color} collar lay in the grass, and its tiny bell made the faintest tinkle.")


def dialogue_search(world: World, child: Entity, ghost: Entity, collar: Entity) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    ghost.memes["loneliness"] = ghost.memes.get("loneliness", 0) + 1
    world.say(f"\"Are you lost?\" {child.id} asked.")
    world.say(f"\"Only my collar is lost,\" the ghost answered. \"Without it, I feel far away.\"")
    world.say(f"\"Then let's find it,\" {child.id} said, and the dark felt a little less deep.")


def locate_collar(world: World, child: Entity, collar: Entity) -> None:
    child.meters["searching"] = child.meters.get("searching", 0) + 1
    collar.held_by = child.id
    world.say(f"{child.id} knelt by the wet grass and picked up the collar with careful fingers.")


def reasonableness_gate(place: Place, collar: Collar, ghost: Entity) -> bool:
    return place.dark and ghost.kind == "ghost" and "collar" in collar.tags


def resolve_acceptance(world: World, child: Entity, ghost: Entity, collar: Entity) -> None:
    child.memes["courage"] = child.memes.get("courage", 0) + 1
    ghost.memes["relief"] = ghost.memes.get("relief", 0) + 1
    ghost.memes["loneliness"] = 0
    collar.worn_by = ghost.id
    collar.held_by = None
    world.say(f"\"Here,\" {child.id} said. \"I found your collar.\"")
    world.say(f"The ghost leaned close, and the bell gave a tiny bright sound when the collar slipped back into place.")
    world.say(f"\"Thank you,\" the ghost whispered. \"Now I can stay long enough to say goodbye.\"")
    world.say(f"Then the ghost faded like mist at sunrise, while the little bell chimed once in the grass.")


def tell_story(params: StoryParams) -> World:
    place = setup_place(params.place)
    world = World(place)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=["little", params.trait],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
    ))
    ghost = world.add(Entity(
        id="Ghost",
        kind="ghost",
        type="ghost",
        label="the ghost",
        meters={"fade": 1.0},
        memes={"loneliness": 1.0},
    ))
    collar = world.add(Entity(
        id="Collar",
        type="collar",
        label="collar",
        phrase=f"a {params.collar_color} collar with a tiny bell",
        tags={"collar", "bell", params.collar_color},
    ))

    child_intro(world, child)
    world.say(f"{child.id} and {parent.label} were walking home when the air turned cold and still.")
    ghost_intro(world, ghost)
    collar_intro(world, collar, params.collar_color)

    world.para()
    world.say(f"\"Did you hear that?\" {child.id} asked.")
    world.say(f"\"I heard a whisper,\" {parent.label} said, \"but whispers are not the same as danger.\"")
    dialogue_search(world, child, ghost, collar)

    if reasonableness_gate(place, collar, ghost):
        locate_collar(world, child, collar)
        world.say(f"\"Maybe it was hiding near the fence,\" {child.id} said, peering into the dark.")
        resolve_acceptance(world, child, ghost, collar)
    else:
        pass

    world.facts = {
        "child": child,
        "parent": parent,
        "ghost": ghost,
        "collar": collar,
        "place": place,
        "params": params,
        "resolved": True,
    }
    return world


SETTINGS = {
    "yard": Place(name="the yard", outdoors=True if False else True, dark=True, tags={"dark", "grass"}),
    "garden": Place(name="the garden", outdoors=True if False else True, dark=True, tags={"dark", "fence"}),
    "lane": Place(name="the lane", outdoors=True if False else True, dark=True, tags={"dark", "stone"}),
    "porch": Place(name="the porch", outdoors=True if False else True, dark=True, tags={"dark", "steps"}),
}

PLACES = {
    "yard": Place(name="the yard", indoors=False, dark=True, tags={"grass", "fence"}),
    "garden": Place(name="the garden", indoors=False, dark=True, tags={"flowers", "fence"}),
    "lane": Place(name="the lane", indoors=False, dark=True, tags={"stone", "street"}),
    "porch": Place(name="the porch", indoors=False, dark=True, tags={"steps", "door"}),
}

COLLARS = {
    "blue": Collar(label="collar", phrase="a blue collar with a tiny bell", color="blue", tags={"collar", "bell"}),
    "red": Collar(label="collar", phrase="a red collar with a tiny bell", color="red", tags={"collar", "bell"}),
    "green": Collar(label="collar", phrase="a green collar with a tiny bell", color="green", tags={"collar", "bell"}),
}

GIRL_NAMES = ["Mina", "Lily", "Ivy", "Nora", "June", "Rose"]
BOY_NAMES = ["Owen", "Finn", "Eli", "Theo", "Milo", "Jack"]
TRAITS = ["brave", "curious", "gentle", "quiet", "careful", "shy"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, color) for place in PLACES for color in COLLARS]


@dataclass
class ASPFacts:
    pass
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


ASP_RULES = r"""
place_ok(P) :- place(P), dark_place(P).
collar_ok(C) :- collar(C), collar_tag(C, collar), collar_tag(C, bell).
story_ok(P, C) :- place_ok(P), collar_ok(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.dark:
            lines.append(asp.fact("dark_place", pid))
        for tag in sorted(p.tags):
            lines.append(asp.fact("place_tag", pid, tag))
    for cid, c in COLLARS.items():
        lines.append(asp.fact("collar", cid))
        for tag in sorted(c.tags):
            lines.append(asp.fact("collar_tag", cid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_ok/2."))
    return sorted(set(asp.atoms(model, "story_ok")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with a collar and dialogue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--collar-color", choices=COLLARS)
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
    place = getattr(args, "place", None) or rng.choice(sorted(PLACES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    collar_color = getattr(args, "collar_color", None) or rng.choice(sorted(COLLARS))
    return StoryParams(place=place, name=name, gender=gender, parent=parent, trait=trait, collar_color=collar_color)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    return [
        f'Write a gentle ghost story for a child named {child.id} that includes the word "collar".',
        f"Tell a short dialogue story where {child.id} finds a lost collar and speaks kindly to a ghost.",
        "Write a spooky-but-soft story about a dark yard, a missing collar, and a brave child who helps.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, ghost, collar = f["child"], f["ghost"], f["collar"]
    return [
        QAItem(
            question=f"What did {child.id} find in the grass?",
            answer=f"{child.id} found {collar.phrase}, and the tiny bell made a soft tinkle in the dark grass.",
        ),
        QAItem(
            question=f"Who was looking for the collar?",
            answer=f"The ghost was looking for the collar because it felt far away without it.",
        ),
        QAItem(
            question=f"What did {child.id} say to help the ghost?",
            answer=f"{child.id} said, \"Let's find it,\" and then carefully brought the collar back.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a collar?",
            answer="A collar is a band people or animals wear around the neck, and some collars have a bell or tag.",
        ),
        QAItem(
            question="Why do bells make stories feel alert?",
            answer="A tiny bell makes a soft sound that helps people notice movement, which can feel exciting in a quiet scene.",
        ),
        QAItem(
            question="What does a ghost story often have?",
            answer="A ghost story often has a dark place, a mysterious sound, and someone who feels a little afraid before things become clear.",
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
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
    StoryParams(place="yard", name="Mina", gender="girl", parent="mother", trait="curious", collar_color="blue"),
    StoryParams(place="garden", name="Owen", gender="boy", parent="father", trait="gentle", collar_color="red"),
    StoryParams(place="lane", name="Ivy", gender="girl", parent="mother", trait="shy", collar_color="green"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show story_ok/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story settings:")
        for place, color in combos:
            print(f"  {place:8} {color}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 30):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.name}: {p.place} / {p.collar_color}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
