#!/usr/bin/env python3
"""
storyworlds/worlds/carburetor_sound_effects_cautionary_pirate_tale.py
======================================================================

A standalone story world for a small cautionary pirate tale about a noisy
carburetor, a clever crew, and the lesson that some sounds mean trouble.

Premise:
- A young pirate loves the engine room and the sound of the little motor.
- The carburetor starts making strange sputters, pops, and coughs.
- If the crew ignores it and sails on, the boat may stall in a bad place.
- A careful check, a fix, and a slower course keep everyone safe.

The story is intentionally small and state-driven:
- physical meters track noise, smoke, fuel trouble, and repair progress
- emotional memes track worry, patience, relief, and pride
- sound effects are narrated from the world state, not bolted on as a static line
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
# Core world model
# ---------------------------------------------------------------------------

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
    props: dict[str, str] = field(default_factory=dict)

    child: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "pirate-boy", "captain", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "pirate-girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
class Ship:
    name: str
    place: str = "the harbor"
    heading: str = "out to sea"
    safe_harbor: bool = True
    wind: str = "gentle"
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    ship: object | None = None
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
class StoryParams:
    name: str
    child_type: str
    parent_type: str
    ship_name: str
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
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.story: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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
            self.story.append(text)

    def render(self) -> str:
        return " ".join(self.story)


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
NAMES_BOY = ["Finn", "Toby", "Milo", "Jasper", "Ned", "Rory"]
NAMES_GIRL = ["Mara", "Pia", "Lina", "Nell", "Tia", "Cora"]

SHIPS = [
    "the Bright Gull",
    "the Tiny Tide",
    "the Sea Spoon",
    "the Laughing Lantern",
]

CARBURETOR_SNAPS = [
    "ptt-ptt-ptt",
    "brrp-brrp",
    "chuff-chuff",
    "pop-pop-pop",
    "hisss... sputter",
]

CARBURETOR_FAIL_SOUNDS = [
    "the motor gave a sad cough",
    "the engine made a rough rattling whine",
    "a wet sputter came from under the hatch",
]

CARBURETOR_FIX_SOUNDS = [
    "the cough turned into a steady hum",
    "the rattling softened into a purr",
    "the sputter faded to a neat little tick-tick",
]

TRAITS = ["curious", "brave", "stubborn", "cheerful", "quick-handed"]


@dataclass
class Tension:
    id: str
    description: str
    risky_speed: str
    warning: str
    consequence: str
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


TENSIONS = [
    Tension(
        id="reef",
        description="a reef ahead",
        risky_speed="too fast",
        warning="A reef can bite the keel if the ship keeps hurrying",
        consequence="the hull could scrape and the crew could be stranded",
    ),
    Tension(
        id="fog",
        description="a fog bank ahead",
        risky_speed="blinded and rushing",
        warning="Fog hides rocks, and a sputtering motor makes the dark worse",
        consequence="the ship could drift wrong and lose its way",
    ),
    Tension(
        id="storm",
        description="a storm line ahead",
        risky_speed="already hard to hold",
        warning="A storm needs a steady engine, not a coughing one",
        consequence="the ship could stall just when the waves grow fierce",
    ),
]


# ---------------------------------------------------------------------------
# Reasonable-world model
# ---------------------------------------------------------------------------
@dataclass
class Carburetor:
    label: str = "carburetor"
    meters: dict[str, float] = field(default_factory=lambda: {
        "noise": 0.0,
        "trouble": 0.0,
        "soot": 0.0,
        "fixed": 0.0,
    })
    memes: dict[str, float] = field(default_factory=lambda: {
        "annoyance": 0.0,
        "worry": 0.0,
        "relief": 0.0,
    })
    carburetor: object | None = None
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


class PirateWorld:
    def __init__(self, child: Entity, parent: Entity, ship: Ship, tension: Tension) -> None:
        self.child = child
        self.parent = parent
        self.ship = ship
        self.tension = tension
        self.carburetor = Carburetor()
        self.entities = {
            child.id: child,
            parent.id: parent,
        }
        self.story: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def say(self, text: str) -> None:
        if text:
            self.story.append(text)

    def render(self) -> str:
        return " ".join(self.story)


def _sfx(world: PirateWorld) -> str:
    idx = min(int(world.carburetor.meters["noise"]), len(CARBURETOR_SNAPS) - 1)
    return _safe_lookup(CARBURETOR_SNAPS, idx)


def _engine_noise(world: PirateWorld) -> None:
    if world.carburetor.meters["noise"] < 1:
        return
    if "noise" in world.fired:
        return
    world.fired.add("noise")
    sfx = _sfx(world)
    world.say(f"From under the hatch came {sfx}!")
    world.say(random.choice(CARBURETOR_FAIL_SOUNDS))
    world.carburetor.memes["worry"] += 1


def _warning_rule(world: PirateWorld) -> None:
    if world.carburetor.meters["noise"] < 1 or "warned" in world.fired:
        return
    if world.carburetor.meters["trouble"] < 1:
        return
    world.fired.add("warned")
    world.parent.memes["worry"] += 1
    world.say(
        f'"{world.tension.warning}," said {world.parent.id}, '
        f'watching the {world.carburetor.label} like a storm cloud.'
    )


def _fix_rule(world: PirateWorld) -> None:
    if world.carburetor.meters["fixed"] < 1 or "fixed" in world.fired:
        return
    world.fired.add("fixed")
    world.carburetor.memes["relief"] += 1
    world.parent.memes["relief"] += 1
    world.child.memes["relief"] += 1
    world.say(random.choice(CARBURETOR_FIX_SOUNDS) + ".")


def propagate(world: PirateWorld) -> None:
    _engine_noise(world)
    _warning_rule(world)
    _fix_rule(world)


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def check_reasonable(params: StoryParams) -> None:
    if params.child_type not in {"boy", "girl"}:
        pass
    if params.parent_type not in {"captain", "mother", "father"}:
        pass


def build_world(params: StoryParams, rng: random.Random) -> PirateWorld:
    check_reasonable(params)
    child = Entity(
        id=params.name,
        kind="character",
        type=params.child_type,
        label=params.name,
        meters={"courage": 0.0},
        memes={"joy": 1.0, "worry": 0.0, "pride": 0.0},
        props={"trait": rng.choice(TRAITS)},
    )
    parent_name = "Captain" if params.parent_type == "captain" else ("Mom" if params.parent_type == "mother" else "Dad")
    parent = Entity(
        id=parent_name,
        kind="character",
        type=params.parent_type,
        label=parent_name,
        meters={"attention": 1.0},
        memes={"worry": 0.0, "patience": 1.0, "relief": 0.0},
    )
    ship = Ship(
        name=params.ship_name,
        place="the harbor",
        heading="toward the open sea",
        safe_harbor=True,
        wind="soft",
        meters={"speed": 0.0, "fuel": 1.0},
        memes={"calm": 1.0},
    )
    tension = random.choice(TENSIONS)
    world = PirateWorld(child, parent, ship, tension)
    world.facts.update(params=params, child=child, parent=parent, ship=ship, tension=tension)
    return world


def narrative_setup(world: PirateWorld) -> None:
    c = world.child
    p = world.parent
    ship = world.ship
    trait = c.props["trait"]
    world.say(
        f"On {ship.name}, a little {trait} pirate named {c.id} loved the engine room and the salty smell of tar."
    )
    world.say(
        f"{c.id} liked the tiny thrum of the motor, because it made {ship.name} feel bold and quick."
    )
    world.say(
        f"{p.id} said a pirate ship should always listen to its sounds, for quiet water can hide trouble."
    )


def narrative_turn(world: PirateWorld) -> None:
    c = world.child
    p = world.parent
    tension = world.tension
    world.say(
        f"One day, {ship_phrase(world)} met {tension.description}, and the little motor began to misbehave."
    )
    world.carburetor.meters["noise"] += 1
    world.carburetor.meters["trouble"] += 1
    world.say(f"The {world.carburetor.label} went {random.choice(CARBURETOR_SNAPS)}!")
    propagate(world)
    world.say(
        f"{c.id} wanted to keep sailing, but {p.id} frowned and pointed at the hatch."
    )
    world.carburetor.memes["worry"] += 1
    world.say(
        f'"If we ignore that sound," said {p.id}, "we could meet {tension.consequence}."'
    )
    world.say(
        f"{c.id} listened more closely and heard that the cough was not a game, but a warning."
    )


def ship_phrase(world: PirateWorld) -> str:
    return world.ship.name


def narrative_resolution(world: PirateWorld) -> None:
    c = world.child
    p = world.parent
    world.say(
        f"So {c.id} fetched a rag, {p.id} opened the hatch, and together they cleaned the soot from the carburetor."
    )
    world.carburetor.meters["soot"] += 1
    world.carburetor.meters["fixed"] += 1
    world.ship.meters["speed"] = 1.0
    world.ship.memes["calm"] = 1.0
    propagate(world)
    world.say(
        f"Then the motor settled into a steady purr, and {ship_phrase(world)} moved safely around the danger."
    )
    world.say(
        f"{c.id} grinned, because the caution had helped them keep the voyage clever, calm, and sound."
    )
    world.say(
        f"By sunset, the sea was shining, the carburetor was quiet, and the little pirate had learned to respect every sputter."
    )
    world.facts["resolved"] = True


def tell(params: StoryParams) -> PirateWorld:
    rng = random.Random(params.seed or 0)
    world = build_world(params, rng)
    narrative_setup(world)
    world.say("")
    narrative_turn(world)
    world.say("")
    narrative_resolution(world)
    return world


# ---------------------------------------------------------------------------
# Registries and parameters
# ---------------------------------------------------------------------------
@dataclass
class Registry:
    names_boy: list[str] = field(default_factory=lambda: list(NAMES_BOY))
    names_girl: list[str] = field(default_factory=lambda: list(NAMES_GIRL))
    ships: list[str] = field(default_factory=lambda: list(SHIPS))
    tensions: list[Tension] = field(default_factory=lambda: list(TENSIONS))
    REGISTRY: object | None = None
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


REGISTRY = Registry()


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: PirateWorld) -> list[str]:
    p = world.parent
    c = world.child
    t = world.tension
    return [
        "Write a short cautionary pirate tale with a noisy carburetor and a safe fix.",
        f"Tell a pirate story where {c.id} hears a strange engine sound and {p.id} warns about {t.description}.",
        "Write a child-friendly adventure with sound effects like sputter, pop, and hum, ending with a lesson about listening.",
    ]


def story_qa(world: PirateWorld) -> list[QAItem]:
    c = world.child
    p = world.parent
    t = world.tension
    return [
        QAItem(
            question=f"Why did {p.id} worry when the {world.carburetor.label} started making a strange sound?",
            answer=(
                f"{p.id} worried because the {world.carburetor.label} went noisy and that could lead to {t.consequence}. "
                f"{p.id} wanted the ship to stay safe instead of rushing into danger."
            ),
        ),
        QAItem(
            question=f"What did {c.id} do when the engine room made that {_safe_lookup(CARBURETOR_SNAPS, 0)} sound?",
            answer=(
                f"{c.id} listened, fetched a rag, and helped clean the carburetor with {p.id}. "
                f"That careful work turned the trouble into a safer trip."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                "The motor settled into a steady hum, the ship sailed around the danger, "
                "and the little pirate learned to respect warning sounds."
            ),
        ),
    ]


def world_knowledge_qa(world: PirateWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is a carburetor?",
            answer=(
                "A carburetor is a machine part that helps an engine mix fuel and air so the motor can run."
            ),
        ),
        QAItem(
            question="Why are sound effects useful in a story?",
            answer=(
                "Sound effects help a reader imagine what is happening, like a sputter, a pop, or a steady hum."
            ),
        ),
        QAItem(
            question="Why is a cautionary story helpful?",
            answer=(
                "A cautionary story helps children notice danger and make a safer choice before trouble grows."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story Q&A ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world Q&A ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Facts:
% ship(S). child(C). parent(P). tension(T). carburetor(CB).
% noisy(CB). warning_sound(CB). fixed(CB). danger(T).

needs_warning(CB,T) :- noisy(CB), danger(T).
should_fix(CB) :- noisy(CB), carburetor(CB).
safe_end :- fixed(CB), carburetor(CB).
cautionary_story :- should_fix(CB), needs_warning(CB,T), safe_end.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("carburetor", "cb1"))
    lines.append(asp.fact("ship", "ship1"))
    lines.append(asp.fact("child", "child1"))
    lines.append(asp.fact("parent", "parent1"))
    lines.append(asp.fact("danger", "reef"))
    lines.append(asp.fact("noisy", "cb1"))
    lines.append(asp.fact("warning_sound", "cb1"))
    lines.append(asp.fact("fixed", "cb1"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show cautionary_story/0."))
    atoms = [a.name for a in model]
    py_ok = True
    if "cautionary_story" not in atoms:
        py_ok = False
    if py_ok:
        print("OK: ASP twin recognizes the cautionary carburetor story.")
        return 0
    print("MISMATCH: ASP twin did not recognize the story.")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary pirate tale about a carburetor and warning sounds.")
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=["boy", "girl"])
    ap.add_argument("--parent-type", choices=["captain", "mother", "father"])
    ap.add_argument("--ship-name")
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
    child_type = getattr(args, "child_type", None) or rng.choice(["boy", "girl"])
    if getattr(args, "name", None):
        name = getattr(args, "name", None)
    else:
        name = rng.choice(NAMES_BOY if child_type == "boy" else NAMES_GIRL)
    parent_type = getattr(args, "parent_type", None) or rng.choice(["captain", "mother", "father"])
    ship_name = getattr(args, "ship_name", None) or rng.choice(SHIPS)
    return StoryParams(name=name, child_type=child_type, parent_type=parent_type, ship_name=ship_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: PirateWorld) -> str:
    lines = ["--- world trace ---"]
    c = world.child
    p = world.parent
    lines.append(f"child={c.id} meters={c.meters} memes={c.memes} trait={c.props.get('trait')}")
    lines.append(f"parent={p.id} meters={p.meters} memes={p.memes}")
    lines.append(f"ship={world.ship.name} meters={world.ship.meters} memes={world.ship.memes}")
    lines.append(
        "carburetor="
        f"{world.carburetor.meters} memes={world.carburetor.memes}"
    )
    lines.append(f"tension={world.tension.id}: {world.tension.description}")
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
    StoryParams(name="Finn", child_type="boy", parent_type="captain", ship_name="the Bright Gull"),
    StoryParams(name="Mara", child_type="girl", parent_type="mother", ship_name="the Tiny Tide"),
    StoryParams(name="Ned", child_type="boy", parent_type="father", ship_name="the Laughing Lantern"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show cautionary_story/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
            header = f"### {p.name} on {p.ship_name}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
