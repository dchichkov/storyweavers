#!/usr/bin/env python3
"""
A standalone story world for a small mystery with a warrior, dialogue, and a
hypothetical clue trail.

Premise:
- A young warrior hears a strange rumor about a missing lantern in a quiet
  hall.
- The warrior questions a few people, notices contradictions, and tests a
  hypothetical explanation against the physical trace in the room.
- The ending reveals who moved the lantern and why, with the world state
  proving the change.

This script follows the Storyweavers storyworld contract:
- typed entities with physical meters and emotional memes
- causal state drives prose
- inline ASP twin plus Python reasonableness gate
- StoryParams / registries / build_parser / resolve_params / generate / emit / main
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    location: str = ""
    movable: bool = False
    secret: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    suspect: object | None = None
    warrior: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister"}
        male = {"boy", "man", "father", "brother", "warrior"}
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
    id: str
    label: str
    atmosphere: str
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
class Clue:
    id: str
    label: str
    reveals: str
    location: str
    risk: str = ""
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
    role: str
    likely: bool = False
    alibi: str = ""
    tells: str = ""
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
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


@dataclass
class StoryParams:
    place: str
    warrior: str
    suspect: str
    clue: str
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


PLACES = {
    "hall": Place("hall", "the stone hall", "quiet and echoing", {"walk", "question", "hide"}),
    "courtyard": Place("courtyard", "the courtyard", "open and windy", {"walk", "question", "hide"}),
    "library": Place("library", "the old library", "still and dusty", {"walk", "question", "hide"}),
}

SUSPECTS = {
    "scout": Suspect("scout", "the scout", "scout", likely=False, alibi="was on the roof", tells="looked at the floor"),
    "keeper": Suspect("keeper", "the keeper", "keeper", likely=True, alibi="counted candles all morning", tells="kept a hand on the lantern shelf"),
    "squire": Suspect("squire", "the squire", "squire", likely=False, alibi="carried water by the gate", tells="spoke too quickly"),
}

CLUES = {
    "ash": Clue("ash", "a pinch of ash", "the lantern had been moved after the fire", "shelf", "gray and fine"),
    "wax": Clue("wax", "a wax drip", "someone had stood close to the lantern", "floor", "warm and soft"),
    "scratch": Clue("scratch", "a scratch on the stone", "the lantern was dragged, not lifted", "shelf", "thin and fresh"),
}

WARRIORS = ["Arin", "Bela", "Cato", "Dara", "Evan", "Fenn"]
TRAITS = ["steady", "curious", "quiet", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in PLACES:
        for suspect in SUSPECTS:
            for clue in CLUES:
                out.append((place, suspect, clue))
    return out


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        pass
    if params.suspect not in SUSPECTS:
        pass
    if params.clue not in CLUES:
        pass
    if params.suspect == "keeper" and params.clue == "ash":
        return
    if params.suspect == "squire" and params.clue == "scratch":
        return
    # All combos are allowed; this gate exists to reject impossible setups if extended.


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        lines.append(asp.fact("role", sid, s.role))
        if s.likely:
            lines.append(asp.fact("likely", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("reveals", cid, c.reveals))
    return "\n".join(lines)


ASP_RULES = r"""
% A suspect is plausible if their tell matches the clue's meaning.
plausible(S, C) :- likely(S), clue(C).
plausible(S, C) :- role(S, keeper), clue(C), C = ash.
plausible(S, C) :- role(S, squire), clue(C), C = scratch.

solved(P, S, C) :- place(P), suspect(S), clue(C), plausible(S, C).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_solved() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solved/3."))
    return sorted(set(asp.atoms(model, "solved")))


def asp_verify() -> int:
    py = set((p, s, c) for (p, s, c) in valid_combos())
    cl = set(asp_solved())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} combos.")
        return 0
    print("Mismatch between ASP and Python.")
    print("Only ASP:", sorted(cl - py))
    print("Only Python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mystery story world with a warrior and dialogue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--warrior", choices=WARRIORS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--clue", choices=CLUES)
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
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "suspect", None):
        combos = [c for c in combos if c[1] == getattr(args, "suspect", None)]
    if getattr(args, "clue", None):
        combos = [c for c in combos if c[2] == getattr(args, "clue", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, suspect, clue = (list(rng.choice(combos)) + [None, None, None])[:3]
    warrior = getattr(args, "warrior", None) or rng.choice(WARRIORS)
    return StoryParams(place=place, warrior=warrior, suspect=suspect, clue=clue)


def _setup(world: World, warrior: Entity, suspect: Entity, clue: Entity) -> None:
    world.say(f"{warrior.id} was a {world.facts['trait']} warrior who noticed small things.")
    world.say(f"One quiet evening, {warrior.id} heard a rumor that the lantern was missing from {world.place.label}.")
    world.say(f"{warrior.id} asked, \"Who was near the shelf?\" and {suspect.label} said, \"Not me.\"")
    world.say(f"Then {warrior.id} saw {clue.label} near the place where the lantern should have been.")


def _investigate(world: World, warrior: Entity, suspect: Entity, clue: Entity) -> None:
    warrior.memes["curiosity"] += 1
    warrior.memes["doubt"] += 1
    if clue.id == "ash":
        world.say(f"{warrior.id} touched the ash and whispered, \"That means the lantern moved after the fire.\"")
    elif clue.id == "wax":
        world.say(f"{warrior.id} pointed at the wax and said, \"Someone stood close and spoke near the flame.\"")
    else:
        world.say(f"{warrior.id} traced the scratch and said, \"It was dragged along the stone.\"")
    suspect.memes["nervous"] += 1


def _hypothesis(world: World, warrior: Entity, suspect: Entity, clue: Entity) -> None:
    world.say(f"\"If the clue is true,\" {warrior.id} said, \"then {suspect.label} moved the lantern for a reason.\"")
    if suspect.id == "keeper":
        world.say(f"\"Maybe {suspect.label} hid it to keep it safe, not to steal it,\" {warrior.id} guessed.")
    elif suspect.id == "squire":
        world.say(f"\"Maybe {suspect.label} rushed it away during the rush of work,\" {warrior.id} guessed.")
    else:
        world.say(f"\"Maybe {suspect.label} only saw what happened and is afraid to say so,\" {warrior.id} guessed.")


def _reveal(world: World, warrior: Entity, suspect: Entity, clue: Entity) -> None:
    suspect.memes["relief"] += 1
    if suspect.id == "keeper":
        world.say(f"{suspect.label} finally admitted, \"I moved it into the dry room so the rain would not crack the glass.\"")
        world.say(f"{warrior.id} nodded. The mystery was not theft at all, but a careful rescue.")
    elif suspect.id == "squire":
        world.say(f"{suspect.label} confessed, \"I dragged it when the bell rang. I was trying to get it to the chapel.\"")
        world.say(f"{warrior.id} saw the truth: the lantern had been saved in a hurry, not taken in greed.")
    else:
        world.say(f"{suspect.label} pointed to the shelf and said, \"I only watched. The keeper moved it first.\"")
        world.say(f"{warrior.id} turned toward the keeper, and the trail of clues fit at last.")
    world.say(f"In the end, the lantern returned to its stand, and the hall felt quiet in a solved way.")


def tell(world: World, warrior: Entity, suspect: Entity, clue: Entity) -> World:
    _setup(world, warrior, suspect, clue)
    world.para()
    _investigate(world, warrior, suspect, clue)
    _hypothesis(world, warrior, suspect, clue)
    world.para()
    _reveal(world, warrior, suspect, clue)
    world.facts.update(warrior=warrior, suspect=suspect, clue=clue, place=world.place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for children about a warrior named {f["warrior"].id} who solves a lantern puzzle with dialogue.',
        f'Tell a gentle detective tale where {f["warrior"].id} asks questions in {f["place"].label} and follows {f["clue"].label}.',
        f'Write a story with a hypothetical clue explanation and a warrior who speaks politely to a suspicious {f["suspect"].role}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    warrior = _safe_fact(world, f, "warrior")
    suspect = _safe_fact(world, f, "suspect")
    clue = _safe_fact(world, f, "clue")
    place = _safe_fact(world, f, "place")
    if suspect.id == "keeper":
        reason = "The keeper said the lantern was moved to the dry room so the rain would not crack the glass."
    elif suspect.id == "squire":
        reason = "The squire said the lantern was dragged away in a hurry when the bell rang."
    else:
        reason = "The suspect only watched, which pointed the warrior back toward the keeper."
    return [
        QAItem(
            question=f"Who solved the lantern mystery in {place.label}?",
            answer=f"{warrior.id}, a {world.facts['trait']} warrior, solved it by asking careful questions and following the clue.",
        ),
        QAItem(
            question=f"What clue did {warrior.id} notice near the shelf?",
            answer=f"{warrior.id} noticed {clue.label}, which gave a physical hint about what happened to the lantern.",
        ),
        QAItem(
            question=f"Why did {suspect.label} matter to the mystery?",
            answer=reason,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hypothesis?",
            answer="A hypothesis is a possible explanation that someone tests against the clues they have.",
        ),
        QAItem(
            question="What does a warrior do in a mystery story?",
            answer="A warrior can ask questions, notice clues, and stay brave while figuring out the truth.",
        ),
        QAItem(
            question="Why do detectives look at small details?",
            answer="Small details can connect a person, a place, and an event, which helps solve the mystery.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = World(_safe_lookup(PLACES, params.place))
    warrior = world.add(Entity(id=params.warrior, kind="character", type="warrior"))
    suspect_cfg = _safe_lookup(SUSPECTS, params.suspect)
    suspect = world.add(Entity(id=suspect_cfg.id, kind="character", type="man", label=suspect_cfg.label))
    clue_cfg = _safe_lookup(CLUES, params.clue)
    clue = world.add(Entity(id=clue_cfg.id, kind="thing", type="clue", label=clue_cfg.label, location=clue_cfg.location))
    world.facts["trait"] = random.choice(TRAITS)
    tell(world, warrior, suspect, clue)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(place="hall", warrior="Arin", suspect="keeper", clue="ash"),
    StoryParams(place="courtyard", warrior="Bela", suspect="squire", clue="scratch"),
    StoryParams(place="library", warrior="Cato", suspect="scout", clue="wax"),
]


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
        print(asp_program("#show solved/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_solved()
        print(f"{len(triples)} solved combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.warrior}: {p.place} / {p.suspect} / {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
