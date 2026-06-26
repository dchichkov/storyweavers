#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/pasta_officer_indian_rhyme_whodunit.py
===============================================================================================================

A small whodunit-style story world with rhyme, pasta, and an officer who
solves a gentle mystery in an Indian restaurant kitchen.

Seed-tale premise:
- A pot of pasta goes missing.
- An officer investigates with careful questions.
- The answer is hidden in simple clues: sauce, shoes, and who had the key.

The world is built as a tiny simulation with meters and memes:
- meters track physical facts like pasta amount, sauce stains, and distance to clues
- memes track emotional facts like worry, pride, relief, and suspicion

The story is child-facing, complete, and lightly rhymed.
"""

from __future__ import annotations

import argparse
import dataclasses
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
# Core world entities
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    chef: object | None = None
    child: object | None = None
    officer: object | None = None
    pasta: object | None = None
    pot: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"distance": 0.0}
        if not self.memes:
            self.memes = {"calm": 0.0, "worry": 0.0, "pride": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "woman", "chef", "server"}
        masculine = {"boy", "man", "officer", "detective"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id
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
class Location:
    id: str
    label: str
    indoors: bool = True
    mood: str = ""
    affords: set[str] = field(default_factory=set)
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
class Suspect:
    id: str
    label: str
    type: str
    motive: str
    clue: str
    alibi: str
    guilty: bool = False
    rhyme: str = ""
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


class World:
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.suspects: dict[str, Suspect] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.trace_log: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_suspect(self, sus: Suspect) -> Suspect:
        self.suspects[sus.id] = sus
        return sus

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

    def note(self, msg: str) -> None:
        self.trace_log.append(msg)


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    suspect: str
    clue: str
    name: str
    officer_name: str
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


LOCATIONS = {
    "restaurant": Location(
        id="restaurant",
        label="the small Indian restaurant kitchen",
        indoors=True,
        mood="warm and busy",
        affords={"cook", "serve", "search"},
    ),
    "trainstation": Location(
        id="trainstation",
        label="the station cafe",
        indoors=True,
        mood="echoey and bright",
        affords={"cook", "serve", "search"},
    ),
}

SUSPECTS = {
    "server": Suspect(
        id="server",
        label="the server",
        type="server",
        motive="wanted to hurry the lunch rush",
        clue="a spoon with tomato dots",
        alibi="was carrying drinks when the pasta vanished",
        rhyme="near the chair, then elsewhere",
    ),
    "chef": Suspect(
        id="chef",
        label="the chef",
        type="chef",
        motive="wanted the stove cleared fast",
        clue="a floury apron string",
        alibi="had stirred the sauce all morning",
        rhyme="stir and twirl, no time to hurl",
    ),
    "visitor": Suspect(
        id="visitor",
        label="the visitor",
        type="thing",
        motive="wanted to peek in and taste a spoonful",
        clue="a sticky shoe print",
        alibi="had been near the door, not the pot",
        rhyme="by the mat, not by the vat",
    ),
}

CLUES = {
    "spoon": "a spoon with tomato dots",
    "apron": "a floury apron string",
    "shoe": "a sticky shoe print",
}

NAMES = ["Asha", "Mina", "Ira", "Niko", "Leela", "Ravi", "Pia", "Arun"]
OFFICERS = ["Officer June", "Officer Noor", "Officer Patel", "Officer Dev"]
TRAITS = ["careful", "kind", "bright", "steady"]


# ---------------------------------------------------------------------------
# Story model helpers
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    loc = _safe_lookup(LOCATIONS, params.place)
    world = World(loc)

    officer = world.add(Entity(id="officer", kind="character", type="officer", label=params.officer_name))
    chef = world.add(Entity(id="chef", kind="character", type="chef", label="the chef"))
    child = world.add(Entity(id="child", kind="character", type="girl", label=params.name))
    pasta = world.add(Entity(
        id="pasta",
        kind="thing",
        type="thing",
        label="pasta",
        phrase="a steaming bowl of pasta",
        owner="chef",
        meters={"amount": 0.0, "warmth": 0.0, "distance": 0.0},
        memes={"worry": 0.0, "pride": 0.0, "relief": 0.0},
    ))
    pot = world.add(Entity(
        id="pot",
        kind="thing",
        type="thing",
        label="pot",
        phrase="the big pot",
        owner="chef",
        meters={"empty": 0.0, "distance": 0.0},
    ))
    world.add(Entity(id="spoon", kind="thing", type="thing", label="spoon", phrase="a little spoon"))
    world.facts.update(officer=officer, chef=chef, child=child, pasta=pasta, pot=pot)
    return world


def rhyme_pair(a: str, b: str) -> str:
    return f"{a} / {b}"


def suspect_rhyme(suspect: Suspect) -> str:
    return suspect.rhyme


def narrate_setup(world: World, params: StoryParams) -> None:
    officer: Entity = _safe_fact(world, world.facts, "officer")  # type: ignore[assignment]
    chef: Entity = _safe_fact(world, world.facts, "chef")  # type: ignore[assignment]
    child: Entity = _safe_fact(world, world.facts, "child")  # type: ignore[assignment]
    pasta: Entity = _safe_fact(world, world.facts, "pasta")  # type: ignore[assignment]

    world.say(f"At {world.location.label}, the air was {world.location.mood}, and the pots sat in a row.")
    world.say(f"{child.name_or_label()} loved the smell of pasta, with sauce that sparkled like sunlit glass.")
    world.say(f"The chef kept a careful pot ready, but one little bowl had gone missing from the pass.")
    world.say(f"Then {officer.name_or_label()} arrived with a notebook and a neat little hat.")
    world.say(f'"If pasta is gone, I will find the place," said {officer.name_or_label()}, "so let us begin with grace."')
    pasta.memes["worry"] += 1
    chef.memes["worry"] += 1
    officer.memes["calm"] += 1


def investigate(world: World, params: StoryParams) -> Suspect:
    officer: Entity = _safe_fact(world, world.facts, "officer")  # type: ignore[assignment]
    chef: Entity = _safe_fact(world, world.facts, "chef")  # type: ignore[assignment]
    child: Entity = _safe_fact(world, world.facts, "child")  # type: ignore[assignment]
    suspect = _safe_lookup(SUSPECTS, params.suspect)

    world.para()
    world.say(f"{officer.name_or_label()} asked the chef, the server, and the visitor to stand in a neat small line.")
    world.say(f'"Where were you when the pasta went?" the officer asked. "I ask in rhyme, and I ask it slow."')
    world.say(f"The clues were tiny but clear: {suspect.clue}, a glance, and a place where sauce might flow.")

    if params.clue == "spoon":
        world.say(f"A spoon with tomato dots pointed toward the server, who had carried bowls away from the door.")
        world.facts["matched"] = "server"
    elif params.clue == "apron":
        world.say(f"A floury apron string pointed toward the chef, though the chef looked worried and not at all sore.")
        world.facts["matched"] = "chef"
    else:
        world.say(f"A sticky shoe print led to the visitor, who had tiptoed near the mat and then toward the floor.")
        world.facts["matched"] = "visitor"

    world.say(f'"One clue can mislead," said {officer.name_or_label()}, "but three little facts can open a locked-up gate."')
    world.say(f"The child watched closely, because whodunits are better when the smallest observer can help the case.")
    return suspect


def reveal(world: World, params: StoryParams, suspect: Suspect) -> None:
    officer: Entity = _safe_fact(world, world.facts, "officer")  # type: ignore[assignment]
    chef: Entity = _safe_fact(world, world.facts, "chef")  # type: ignore[assignment]
    child: Entity = _safe_fact(world, world.facts, "child")  # type: ignore[assignment]
    pasta: Entity = _safe_fact(world, world.facts, "pasta")  # type: ignore[assignment]

    world.para()
    guilty = params.suspect == world.facts["matched"]
    if guilty:
        world.say(f"{officer.name_or_label()} smiled. " + f'"The clue fits the culprit," the officer said, "and the case is now bright."')
        world.say(f"It was {suspect.label}, and the reason was plain: {suspect.motive}.")
        world.say(f"{suspect.label.capitalize()} gave a small sigh and admitted it in a whisper-quiet light.")
        world.say(f"Still, the pasta was safe: it had only been moved to a warming shelf by the sink.")
        chef.memes["relief"] += 1
        pasta.meters["distance"] = 1.0
        pasta.memes["relief"] += 1
    else:
        world.say(f"{officer.name_or_label()} shook {officer.pronoun('possessive')} head. " + f'"The first clue was clever, but not the right art."')
        world.say(f"The real answer was {suspect.label}, because {suspect.alibi} and {suspect.clue} matched the start.")
        world.say(f"Then the missing pasta was found on a tray beside the oven, not stolen away.")
        chef.memes["relief"] += 1
        pasta.meters["distance"] = 1.0
        pasta.memes["relief"] += 1

    world.say(f'"No more frown," said {officer.name_or_label()}. "The bowl is found, and the ending is sound."')
    world.say(f"{child.name_or_label()} clapped once, and the chef set out plates so dinner could begin.")
    world.say(f"In the warm little kitchen, the pasta came back, and the case closed with a grin.")


def tell(params: StoryParams) -> World:
    world = build_world(params)
    narrate_setup(world, params)
    investigate(world, params)
    reveal(world, params, _safe_lookup(SUSPECTS, params.suspect))
    return world


# ---------------------------------------------------------------------------
# Validation and ASP twin
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in LOCATIONS:
        for suspect in SUSPECTS:
            for clue in CLUES:
                if clue == "spoon" and suspect == "server":
                    combos.append((place, suspect, clue))
                elif clue == "apron" and suspect == "chef":
                    combos.append((place, suspect, clue))
                elif clue == "shoe" and suspect == "visitor":
                    combos.append((place, suspect, clue))
    return combos


ASP_RULES = r"""
valid(Place, Suspect, Clue) :- place(Place), suspect(Suspect), clue(Clue), match(Suspect, Clue).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in LOCATIONS:
        lines.append(asp.fact("place", p))
    for s in SUSPECTS:
        lines.append(asp.fact("suspect", s))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for s, clue in (("server", "spoon"), ("chef", "apron"), ("visitor", "shoe")):
        lines.append(asp.fact("match", s, clue))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    params: StoryParams = _safe_fact(world, world.facts, "params")  # type: ignore[assignment]
    return [
        f"Write a short whodunit for children about {params.name}, {params.officer_name}, and missing pasta.",
        f"Tell a rhyming mystery set in {world.location.label} where an officer solves who moved the pasta.",
        f"Write a gentle detective story using the words pasta, officer, and Indian, and end with the answer revealed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = _safe_fact(world, world.facts, "params")  # type: ignore[assignment]
    matched = _safe_fact(world, world.facts, "matched")
    officer: Entity = _safe_fact(world, world.facts, "officer")  # type: ignore[assignment]
    child: Entity = _safe_fact(world, world.facts, "child")  # type: ignore[assignment]
    suspect = _safe_lookup(SUSPECTS, params.suspect)
    return [
        QAItem(
            question=f"Who solved the missing pasta mystery in {world.location.label}?",
            answer=f"{officer.name_or_label()} solved it by asking careful questions and following the clue."
        ),
        QAItem(
            question=f"What clue pointed to {suspect.label}?",
            answer=f"The clue was {suspect.clue}, and it matched the evidence the officer found."
        ),
        QAItem(
            question=f"Was the pasta truly stolen?",
            answer="No. The pasta was only moved to a safe spot near the oven, so dinner could still happen."
        ),
        QAItem(
            question=f"How did {child.name_or_label()} help?",
            answer=f"{child.name_or_label()} watched closely and paid attention to the clues, which helped the officer think clearly."
        ),
        QAItem(
            question=f"Why did the officer speak in rhyme?",
            answer="The rhymes made the mystery gentle and fun, like a small song that helped everyone listen."
        ),
        QAItem(
            question=f"Did the story mention Indian food?",
            answer="Yes. The kitchen belonged to a small Indian restaurant, and the pasta was part of the warm supper there."
        ),
        QAItem(
            question=f"What happened at the end?",
            answer="The missing pasta was found, the worry faded, and everyone was ready to eat."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is pasta?",
            answer="Pasta is a food made from dough, often shaped like noodles, shells, or spirals, and usually cooked in hot water."
        ),
        QAItem(
            question="What does an officer do?",
            answer="An officer helps keep people safe and may ask questions to solve problems or find out what happened."
        ),
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story that asks who did the thing and then solves the puzzle by the end."
        ),
        QAItem(
            question="What is rhyme?",
            answer="Rhyme is when words sound alike at the end, like cake and lake, or light and night."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    lines.append(f"suspect_match={world.facts.get('matched')}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sampling and generation
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="restaurant", suspect="server", clue="spoon", name="Asha", officer_name="Officer Noor"),
    StoryParams(place="restaurant", suspect="chef", clue="apron", name="Mina", officer_name="Officer Patel"),
    StoryParams(place="trainstation", suspect="visitor", clue="shoe", name="Leela", officer_name="Officer June"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-friendly rhyming whodunit with pasta and an officer.")
    ap.add_argument("--place", choices=LOCATIONS.keys())
    ap.add_argument("--suspect", choices=SUSPECTS.keys())
    ap.add_argument("--clue", choices=CLUES.keys())
    ap.add_argument("--name")
    ap.add_argument("--officer-name", choices=OFFICERS)
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
    if getattr(args, "suspect", None) and getattr(args, "clue", None):
        expected = {"server": "spoon", "chef": "apron", "visitor": "shoe"}[getattr(args, "suspect", None)]
        if getattr(args, "clue", None) != expected:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "suspect", None) is None or c[1] == getattr(args, "suspect", None))
              and (getattr(args, "clue", None) is None or c[2] == getattr(args, "clue", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, suspect, clue = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    officer_name = getattr(args, "officer_name", None) or rng.choice(OFFICERS)
    return StoryParams(place=place, suspect=suspect, clue=clue, name=name, officer_name=officer_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    world.facts["params"] = params
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible mystery combos:\n")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
            header = f"### {p.name}: {p.suspect} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
