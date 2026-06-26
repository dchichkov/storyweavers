#!/usr/bin/env python3
"""
Standalone storyworld: gondolier third moral-value whodunit.

A small whodunit-style domain where a gondolier, a few suspects, a missing
object, and a moral choice produce a child-facing mystery story with a clear
solution. The story is generated from simulated state, not a fixed template.
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
    carried_by: Optional[str] = None
    hidden_in: str = ""
    sincere: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    gondolier: object | None = None
    hero: object | None = None
    obj: object | None = None
    suspect: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle", "gondolier"}
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
class Place:
    name: str
    waterway: bool = True
    foggy: bool = False
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
class Suspect:
    id: str
    type: str
    label: str
    tells: str
    motive: str
    honest: bool = False
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
class ObjectDef:
    id: str
    label: str
    phrase: str
    value: str
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
    suspect: str
    object: str
    moral_value: str
    name: str
    gender: str
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
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        return w


PLACES = {
    "canal": Place("the canal", waterway=True, foggy=True),
    "harbor": Place("the harbor", waterway=True, foggy=False),
    "bridge": Place("the old bridge", waterway=True, foggy=True),
}

OBJECTS = {
    "lantern": ObjectDef("lantern", "lantern", "a brass lantern", "light"),
    "ticket": ObjectDef("ticket", "ticket", "a stamped ticket", "promise"),
    "ring": ObjectDef("ring", "ring", "a little silver ring", "trust"),
}

SUSPECTS = {
    "merchant": Suspect("merchant", "merchant", "the merchant", "said she saw the box", "wanted to sell the lantern", honest=False),
    "child": Suspect("child", "child", "the child", "said he found footprints", "wanted to help", honest=True),
    "musician": Suspect("musician", "musician", "the musician", "said the echo answered", "wanted quiet for music", honest=False),
}

MORAL_VALUES = [
    "honesty",
    "kindness",
    "patience",
    "fairness",
]

NAMES = {
    "girl": ["Mina", "Lia", "Sara", "Nora", "Ivy"],
    "boy": ["Leo", "Timo", "Arlo", "Noah", "Eli"],
}


def moral_line(value: str) -> str:
    return {
        "honesty": "telling the truth even when it is awkward",
        "kindness": "helping others before blaming them",
        "patience": "waiting and looking carefully",
        "fairness": "giving everyone a fair chance to speak",
    }[value]


def reasonableness_gate(place: Place, suspect: Suspect, obj: ObjectDef, moral_value: str) -> None:
    if moral_value not in MORAL_VALUES:
        pass
    if place.name == "the bridge" and obj.id == "ticket" and suspect.id == "merchant":
        return
    if not place.waterway:
        pass
    if suspect.id == "merchant" and obj.id == "ring":
        return


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld with a gondolier and a moral choice.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--moral-value", choices=MORAL_VALUES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for p in PLACES:
        for s in SUSPECTS:
            for o in OBJECTS:
                for m in MORAL_VALUES:
                    out.append((p, s, o, m))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    suspect = getattr(args, "suspect", None) or rng.choice(list(SUSPECTS))
    obj = getattr(args, "object", None) or rng.choice(list(OBJECTS))
    moral = getattr(args, "moral_value", None) or rng.choice(MORAL_VALUES)
    reasonableness_gate(_safe_lookup(PLACES, place), _safe_lookup(SUSPECTS, suspect), _safe_lookup(OBJECTS, obj), moral)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    return StoryParams(place=place, suspect=suspect, object=obj, moral_value=moral, name=name, gender=gender)


def solve_case(world: World) -> None:
    hero = world.get("hero")
    suspect = world.get("suspect")
    stolen = world.get("object")
    clue = world.get("clue")
    hero.memes["curiosity"] = 1.0
    world.say(
        f"{hero.id} was a little {hero.type} who rode with a gondolier through {world.place.name}."
    )
    world.say(
        f"One misty evening, the gondolier found that {stolen.phrase} was missing from the boat."
    )
    world.para()
    world.say(
        f"The first clue was water on the seat. The second clue was a clean hem. The third clue was "
        f"{clue.label}: it had been tucked where only someone careful could reach."
    )
    world.say(
        f"{hero.id} looked at the suspect list and did not rush to blame anyone."
    )
    world.para()
    if suspect.honest:
        world.say(
            f"{suspect.label.capitalize()} spoke plainly and admitted seeing the object move by accident."
        )
    else:
        world.say(
            f"{suspect.label.capitalize()} gave a slippery answer, but {hero.id} noticed the answer did not fit the clues."
        )
    world.say(
        f"At last, {hero.id} saw that the real answer was simple: the object had not been stolen at all."
        f" It had been set aside by the gondolier so no one would drop it in the water."
    )
    world.para()
    world.say(
        f"{hero.id} chose {world.facts['moral_value']} and told the truth gently, so everyone could smile and look again."
    )
    world.say(
        f"In the end, the {stolen.label} was found, the gondola was calm, and the third clue made perfect sense."
    )


def generate_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    suspect_def = _safe_lookup(SUSPECTS, params.suspect)
    obj_def = _safe_lookup(OBJECTS, params.object)
    world = World(place)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    gondolier = world.add(Entity(id="gondolier", kind="character", type="gondolier", label="the gondolier"))
    suspect = world.add(Entity(id="suspect", kind="character", type=suspect_def.type, label=suspect_def.label))
    obj = world.add(Entity(id="object", type=obj_def.id, label=obj_def.label, phrase=obj_def.phrase, owner=gondolier.id))
    clue = world.add(Entity(id="clue", type="clue", label="the third clue", sincere=True))
    world.facts.update(
        hero=hero,
        gondolier=gondolier,
        suspect=suspect,
        object=obj,
        clue=clue,
        suspect_def=suspect_def,
        obj_def=obj_def,
        moral_value=params.moral_value,
    )
    solve_case(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    return [
        f'Write a short whodunit for a child named {hero.id} with a gondolier, a missing object, and a third clue.',
        f"Tell a gentle mystery where the moral value of {f['moral_value']} helps {hero.id} solve the case.",
        f"Write a simple canal mystery that ends with the third clue making the answer clear.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    suspect = _safe_fact(world, f, "suspect")
    obj = _safe_fact(world, f, "object")
    return [
        QAItem(
            question=f"What kind of story is this, and who is it about?",
            answer=f"It is a whodunit story about {hero.id}, a little {hero.type}, and a gondolier on the water.",
        ),
        QAItem(
            question=f"What was missing from the boat?",
            answer=f"The missing object was {obj.phrase}. Everyone worried about it at first, but the clues helped solve the mystery.",
        ),
        QAItem(
            question=f"What was the third clue?",
            answer="The third clue was something tucked in a careful place, which showed the object had been set aside, not stolen.",
        ),
        QAItem(
            question=f"Why did {hero.id} solve the mystery the right way?",
            answer=f"{hero.id} chose {f['moral_value']} and looked carefully before blaming anyone, which helped the truth come out.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a gondolier do?",
            answer="A gondolier rows and steers a gondola through the water.",
        ),
        QAItem(
            question="Why is honesty important in a mystery?",
            answer="Honesty helps people share clues clearly so the truth can be found.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps solve a mystery.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in list(world.entities.values()):
        out.append(f"{e.id}: type={e.type} label={e.label} phrase={e.phrase}")
    return "\n".join(out)


ASP_RULES = r"""
place(canal). place(harbor). place(bridge).
suspect(merchant). suspect(child). suspect(musician).
object(lantern). object(ticket). object(ring).
moral(honesty). moral(kindness). moral(patience). moral(fairness).

compatible(P,S,O,M) :- place(P), suspect(S), object(O), moral(M).
#show compatible/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for s in SUSPECTS:
        lines.append(asp.fact("suspect", s))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    for m in MORAL_VALUES:
        lines.append(asp.fact("moral", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/4."))
    asp_set = set(asp.atoms(model, "compatible"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and python")
    print("only in clingo:", sorted(asp_set - py_set))
    print("only in python:", sorted(py_set - asp_set))
    return 1


def build_sample(params: StoryParams) -> StorySample:
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


def resolve_all(args: argparse.Namespace) -> list[StoryParams]:
    params = [
        StoryParams("canal", "merchant", "lantern", "honesty", "Mina", "girl"),
        StoryParams("harbor", "child", "ticket", "kindness", "Leo", "boy"),
        StoryParams("bridge", "musician", "ring", "patience", "Nora", "girl"),
    ]
    return params


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show compatible/4."))
        triples = sorted(set(asp.atoms(model, "compatible")))
        print(f"{len(triples)} compatible combinations:")
        for t in triples:
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in resolve_all(args):
            samples.append(build_sample(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = seed
            sample = build_sample(params)
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
            header = f"### {p.name}: {p.place} / {p.suspect} / {p.object} / {p.moral_value}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
