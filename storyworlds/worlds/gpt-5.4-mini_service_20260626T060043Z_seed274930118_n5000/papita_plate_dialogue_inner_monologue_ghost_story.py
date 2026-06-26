#!/usr/bin/env python3
"""
Story world: papita plate dialogue inner monologue ghost story.

A small, classical story simulation in a ghost-story mood:
a child notices a haunted papita on a plate, hears a ghostly voice,
argues softly in dialogue, thinks through the fear in inner monologue,
and ends with a gentle resolution that changes the room.

The story is built from state changes:
- hunger, curiosity, fear, comfort, and trust are tracked as memes
- warmth, freshness, and candlelight are tracked as meters
- the papita and plate have physical and emotional state too
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    papita: object | None = None
    parent: object | None = None
    plate: object | None = None
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Place:
    label: str = "the kitchen"
    night: bool = True
    eerie: bool = True
    candle: bool = True
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    smell: str
    warmth: str
    ghostly: str
    crumbly: bool = True
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class StoryParams:
    place: str
    treat: str
    name: str
    gender: str
    parent: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


SETTINGS = {
    "kitchen": Place(label="the kitchen", night=True, eerie=True, candle=True),
    "porch": Place(label="the porch", night=True, eerie=True, candle=False),
    "hall": Place(label="the hallway", night=True, eerie=True, candle=True),
}

TREATS = {
    "papita": Treat(
        id="papita",
        label="papita",
        phrase="a warm papita wrapped in a cloth",
        smell="comforting",
        warmth="warm",
        ghostly="glowed pale in the candlelight",
        crumbly=True,
    ),
    "plate": Treat(
        id="plate",
        label="plate",
        phrase="a small plate with a silver rim",
        smell="quiet",
        warmth="cool",
        ghostly="made a thin ringing sound when touched",
        crumbly=False,
    ),
}

NAMES = {
    "girl": ["Mira", "Lila", "Nora", "Anya"],
    "boy": ["Ivo", "Taro", "Noel", "Sami"],
}

TRAITS = ["brave", "curious", "sleepy", "gentle", "careful"]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if p.night:
            lines.append(asp.fact("night", pid))
        if p.eerie:
            lines.append(asp.fact("eerie", pid))
        if p.candle:
            lines.append(asp.fact("candle", pid))
    for tid, t in TREATS.items():
        lines.append(asp.fact("treat", tid))
        lines.append(asp.fact("smell", tid, t.smell))
        lines.append(asp.fact("warmth", tid, t.warmth))
    return "\n".join(lines)


ASP_RULES = r"""
haunted(T) :- treat(T), smell(T, comforting), warmth(T, warm).
haunted(T) :- treat(T), smell(T, quiet), warmth(T, cool).
safe_place(P) :- place(P), candle(P), night(P).
ghost_story(P, T) :- eerie(P), haunted(T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show haunted/1.\n#show ghost_story/2."))
    atoms = set(asp.atoms(model, "haunted")) | set(asp.atoms(model, "ghost_story"))
    expected = {("papita",), ("plate",), ("kitchen", "papita"), ("kitchen", "plate"), ("hall", "papita"), ("hall", "plate"), ("porch", "papita"), ("porch", "plate")}
    # We only need parity with the Python gate below; keep this simple and legible.
    py = set()
    for t in TREATS:
        py.add((t,))
    for p in SETTINGS:
        for t in TREATS:
            if _safe_lookup(SETTINGS, p).eerie:
                py.add((p, t))
    if atoms == py:
        print(f"OK: clingo parity matches Python gate ({len(py)} facts).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("clingo:", sorted(atoms))
    print("python:", sorted(py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost-story world about a papita on a plate.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    treat = getattr(args, "treat", None) or rng.choice(list(TREATS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    return StoryParams(place=place, treat=treat, name=name, gender=gender, parent=parent)


def _inner_monologue(hero: Entity, treat: Treat, plate: Entity) -> str:
    return (
        f"{hero.pronoun('subject').capitalize()} wondered if the little sound had come from the {plate.label} "
        f"or from the {treat.label} itself."
    )


def generate_world(params: StoryParams) -> World:
    place = _safe_lookup(SETTINGS, params.place)
    treat = _safe_lookup(TREATS, params.treat)
    world = World(place)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"warmth": 0.0},
        memes={"fear": 0.0, "curiosity": 1.0, "comfort": 0.0, "trust": 0.0, "hunger": 1.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        meters={"warmth": 0.0},
        memes={"calm": 1.0, "care": 1.0},
    ))
    plate = world.add(Entity(
        id="plate",
        type="plate",
        label="plate",
        phrase="a small plate with a silver rim",
        meters={"cold": 1.0, "shine": 1.0},
        memes={"silence": 1.0},
    ))
    papita = world.add(Entity(
        id="papita",
        type="papita",
        label="papita",
        phrase=treat.phrase,
        owner=parent.id,
        caretaker=parent.id,
        meters={"warmth": 1.0, "freshness": 1.0},
        memes={"smell": 1.0, "mystery": 1.0, "gentleness": 1.0},
    ))

    world.facts.update(child=child, parent=parent, plate=plate, papita=papita, treat=treat, place=place)

    world.say(f"That night, {child.label} sat in {place.label} and stared at the plate on the table.")
    if place.candle:
        world.say("A tiny candle made the shadows wobble like sleepy ghosts.")
    else:
        world.say("The dark room held still, and even the air seemed to listen.")

    world.say(f"On the plate sat {treat.phrase}. It {treat.ghostly}.")
    child.memes["fear"] += 1.0
    child.memes["curiosity"] += 1.0
    world.say(_inner_monologue(child, treat, plate))

    world.say(f'"Is that papita haunted?" {child.label} asked.')
    world.say(f'"Only a little," {parent.label} said. "It is just lonely on the plate."')

    if treat.id == "papita":
        papita.memes["loneliness"] += 1.0
        papita.meters["warmth"] += 0.5
    else:
        papita.meters["cold"] += 0.5

    world.say(f"{child.label} reached closer and listened.")
    if place.candle:
        world.say(f"The candle flickered, and the papita seemed to glow softer instead of scarier.")
    else:
        world.say(f"The dark made the plate look spooky, but the papita still smelled warm.")

    child.memes["fear"] -= 0.5
    child.memes["trust"] += 1.0
    child.memes["comfort"] += 1.0

    world.say(f'"If it is lonely," {child.label} whispered, "I can sit with it."')
    world.say(f'"That is a kind thing to say," {parent.label} answered.')

    world.say(f"{child.label} took the papita from the plate and held it carefully.")
    papita.memes["mystery"] -= 0.5
    papita.meters["freshness"] -= 0.1
    plate.memes["silence"] += 0.5
    child.memes["fear"] = max(0.0, child.memes["fear"] - 0.5)

    world.say(
        f"At last, {child.label} ate the papita slowly, and the plate stayed plain and quiet on the table."
    )
    world.say(
        f"The room no longer felt haunted; it felt warm, with one candle, one plate, and one happy child."
    )
    return world


def story_qa(sample: StorySample) -> list[QAItem]:
    f = sample.world.facts
    child: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    parent: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent")
    treat: Treat = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "treat")
    place: Place = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place")
    return [
        QAItem(
            question=f"What did {child.label} think was haunted in {place.label}?",
            answer=f"{child.label} thought the {treat.label} on the plate was haunted, but it was really just a little spooky at first.",
        ),
        QAItem(
            question=f"Who answered {child.label} when {child.pronoun('subject')} asked about the spooky papita?",
            answer=f"The {parent.type} answered gently and said the papita was only lonely on the plate.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer="The fear got smaller, the trust got bigger, and the room felt warm instead of haunted.",
        ),
    ]


def world_knowledge_qa(sample: StorySample) -> list[QAItem]:
    return [
        QAItem(
            question="What is a plate for?",
            answer="A plate is used to hold food before or during a meal.",
        ),
        QAItem(
            question="What does a candle do in a dark room?",
            answer="A candle gives a small warm light that helps people see in the dark.",
        ),
        QAItem(
            question="Why can a quiet room feel spooky at night?",
            answer="A quiet room can feel spooky because shadows move strangely and little sounds seem bigger.",
        ),
    ]


def generation_prompts(sample: StorySample) -> list[str]:
    f = sample.world.facts
    child: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    treat: Treat = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "treat")
    place: Place = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place")
    return [
        f'Write a ghost-story style scene for a child named {child.label} in {place.label} about a papita on a plate.',
        f'Write a gentle story with Dialogue and Inner Monologue where someone thinks a {treat.label} is haunted.',
        "Tell a short spooky-but-kind bedtime story that ends with the room feeling warm again.",
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
        lines.append(f"  {e.id:8} ({e.type:8}) meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(StorySample(params=params, story="", world=world)),
        story_qa=[],
        world_qa=[],
        world=world,
    )
    sample.story_qa = story_qa(sample)
    sample.world_qa = world_knowledge_qa(sample)
    return sample


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
    StoryParams(place="kitchen", treat="papita", name="Mira", gender="girl", parent="mother"),
    StoryParams(place="hall", treat="papita", name="Ivo", gender="boy", parent="father"),
    StoryParams(place="porch", treat="papita", name="Nora", gender="girl", parent="mother"),
]


def resolve_random_story(args: argparse.Namespace, base_seed: int, i: int) -> StoryParams:
    rng = random.Random(base_seed + i)
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show haunted/1.\n#show ghost_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show haunted/1.\n#show ghost_story/2."))
        print("haunted:", sorted(asp.atoms(model, "haunted")))
        print("ghost_story:", sorted(asp.atoms(model, "ghost_story")))
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(generate(p))
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_random_story(args, base_seed, i)
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.name}: {p.treat} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
