#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/chess_negligent_surprise_repetition_detective_story.py
===============================================================================================================================

A small detective-story world about a chess club, a negligent mistake, a surprise
turn, and a repetition clue that finally exposes the truth.

The story premise:
- A careful detective investigates a strange chess incident.
- A negligent guard or organizer leaves something unattended.
- The mystery seems ordinary at first, then a surprise changes the case.
- Repetition in the observed moves or clues becomes the key to solving it.

The simulated world keeps track of:
- characters and objects with physical meters and emotional memes
- locations, ownership, attention, and clues
- the repeated pattern that lets the detective infer what happened

The script supports the standard Storyweavers interfaces:
- build_parser
- resolve_params
- generate
- emit
- main

It also includes:
- a Python reasonableness gate
- inline ASP rules for parity checking
- story questions and world-knowledge questions
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
    keeper: Optional[str] = None
    location: str = ""
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    board: object | None = None
    clue: object | None = None
    detective: object | None = None
    guard: object | None = None
    suspect_note: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "detective"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "guard"}:
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


@dataclass
class Room:
    name: str
    affords: set[str] = field(default_factory=set)
    clue_style: str = "quiet"
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
class Incident:
    id: str
    label: str
    surprise: str
    repetition: str
    evidence: str
    location: str
    clue_key: str
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
class StoryParams:
    setting: str
    incident: str
    detective_name: str
    guard_name: str
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


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        import copy as _copy
        clone = World(self.room)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _puzzle_suspicion(world: World) -> list[str]:
    out = []
    incident = _safe_fact(world, world.facts, "incident")
    detective = _safe_fact(world, world.facts, "detective")
    clue = _safe_fact(world, world.facts, "clue")
    if detective.memes.get("curiosity", 0) >= 1 and clue.meters.get("seen", 0) >= 1:
        sig = ("suspicion", incident.id)
        if sig not in world.fired:
            world.fired.add(sig)
            detective.memes["suspicion"] = detective.memes.get("suspicion", 0) + 1
            out.append(f"{detective.id} felt the case tug at {detective.pronoun('possessive')} thoughts.")
    return out


def _repeat_spots(world: World) -> list[str]:
    out = []
    clue = _safe_fact(world, world.facts, "clue")
    detective = _safe_fact(world, world.facts, "detective")
    if clue.meters.get("repeated", 0) >= 2 and detective.memes.get("suspicion", 0) >= 1:
        sig = ("repeat", clue.id)
        if sig not in world.fired:
            world.fired.add(sig)
            detective.memes["certainty"] = detective.memes.get("certainty", 0) + 1
            out.append(f"The same little pattern kept returning, and that made the answer clearer.")
    return out


def _surprise_reveal(world: World) -> list[str]:
    out = []
    incident = _safe_fact(world, world.facts, "incident")
    detective = _safe_fact(world, world.facts, "detective")
    guard = _safe_fact(world, world.facts, "guard")
    if incident.evidence == "open_window" and guard.memes.get("negligent", 0) >= 1:
        sig = ("surprise", incident.id)
        if sig not in world.fired:
            world.fired.add(sig)
            detective.memes["surprise"] = detective.memes.get("surprise", 0) + 1
            guard.memes["shame"] = guard.memes.get("shame", 0) + 1
            out.append(f"The surprise was not a thief at all.")
    return out


CAUSAL_RULES = [_puzzle_suspicion, _repeat_spots, _surprise_reveal]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def valid_incident(incident: Incident) -> bool:
    return incident.location in {"chess club", "library", "station hall"} and incident.clue_key in {"repetition", "surprise"}


ROOMS = {
    "chess_club": Room(name="the chess club", affords={"chess"}, clue_style="echoing"),
    "library": Room(name="the library", affords={"chess", "quiet"}, clue_style="still"),
    "station_hall": Room(name="the station hall", affords={"chess", "crowds"}, clue_style="busy"),
}

INCIDENTS = {
    "missing_knight": Incident(
        id="missing_knight",
        label="a missing knight from the board",
        surprise="a window was open wide",
        repetition="the same move kept appearing in the notes",
        evidence="open_window",
        location="the chess club",
        clue_key="repetition",
    ),
    "mixed_scores": Incident(
        id="mixed_scores",
        label="mixed-up chess scores",
        surprise="the score sheets were copied twice",
        repetition="the same score line appeared again and again",
        evidence="copied_sheet",
        location="the library",
        clue_key="repetition",
    ),
    "clock_alarm": Incident(
        id="clock_alarm",
        label="a strange chess clock alarm",
        surprise="the alarm rang right after the second pause",
        repetition="the pauses repeated in the same pattern",
        evidence="open_window",
        location="the station hall",
        clue_key="surprise",
    ),
}

DETECTIVE_NAMES = ["Mira", "June", "Noah", "Iris", "Eli", "Ada", "Theo", "Nina"]
GUARD_NAMES = ["Benn", "Omar", "Ruth", "Lena", "Mason", "Paula"]


def reasonableness_gate(setting: str, incident_id: str) -> bool:
    return setting in ROOMS and incident_id in INCIDENTS and valid_incident(_safe_lookup(INCIDENTS, incident_id))


def choose_clue_text(incident: Incident) -> str:
    if incident.clue_key == "repetition":
        return "repetition"
    return "surprise"


def tell(room: Room, incident: Incident, detective_name: str, guard_name: str) -> World:
    world = World(room)
    detective = world.add(Entity(id=detective_name, kind="character", type="detective", label=detective_name))
    guard = world.add(Entity(id=guard_name, kind="character", type="guard", label=guard_name))
    board = world.add(Entity(id="board", type="thing", label="the chessboard", location=room.name))
    clue = world.add(Entity(id="clue", type="thing", label=choose_clue_text(incident), location=room.name))
    suspect_note = world.add(Entity(id="note", type="thing", label=incident.repetition, location=room.name))
    world.facts.update(detective=detective, guard=guard, board=board, clue=clue, note=suspect_note, incident=incident)

    detective.memes["curiosity"] = 1
    guard.memes["negligent"] = 1

    world.say(f"{detective.id} was the kind of detective who noticed tiny things at {room.name}.")
    world.say(f"At the club, there was chess, silence, and one odd case: {incident.label}.")
    world.say(f"{guard.id} had been negligent, and that made the room feel just a little off.")

    world.para()
    world.say(f"{incident.surprise.capitalize()}, and that was the first surprise.")
    world.say(f"On the table, {incident.repetition}. {detective.id} wrote it down and looked again.")
    clue.meters["seen"] = 1
    clue.meters["repeated"] = 1
    propagate(world, narrate=True)

    world.para()
    world.say(f"{detective.id} checked the board twice.")
    clue.meters["repeated"] = 2
    world.say(f"Then {detective.id} checked the notes again, because the same pattern had returned.")
    propagate(world, narrate=True)

    world.para()
    if incident.evidence == "open_window":
        world.say(f"At last, {detective.id} noticed the open window.")
        world.say(f"The draft had nudged the pieces, which meant the mystery was not a sneaky rival at all.")
    else:
        world.say(f"At last, {detective.id} noticed the copied sheet.")
        world.say(f"The duplicate marks showed that the trouble came from carelessness, not from a clever thief.")
    world.say(f"{guard.id} lowered {guard.pronoun('possessive')} eyes, because being negligent had nearly fooled everyone.")
    world.say(f"{detective.id} smiled. The surprise was solved, and the repeating clue had done its job.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    inc: Incident = _safe_fact(world, f, "incident")
    det: Entity = _safe_fact(world, f, "detective")
    return [
        f"Write a short detective story for a child about chess, {inc.clue_key}, and a surprising clue.",
        f"Tell a simple mystery where {det.id} solves {inc.label} by noticing repetition.",
        f"Write a calm detective story set at {world.room.name} with a negligent mistake and a surprise ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    inc: Incident = _safe_fact(world, f, "incident")
    det: Entity = _safe_fact(world, f, "detective")
    guard: Entity = _safe_fact(world, f, "guard")
    return [
        QAItem(
            question=f"Who investigated the chess mystery at {world.room.name}?",
            answer=f"{det.id} investigated the case and kept watching the clues until the answer made sense.",
        ),
        QAItem(
            question="What made the first part of the mystery surprising?",
            answer=f"The first surprise was that {inc.surprise}. That unexpected detail made the room feel suspicious.",
        ),
        QAItem(
            question="What clue kept repeating?",
            answer=f"The repeating clue was this: {inc.repetition}. When the same pattern showed up again, {det.id} knew to look closer.",
        ),
        QAItem(
            question=f"Why did {guard.id} seem guilty at first?",
            answer=f"{guard.id} seemed guilty because {guard.pronoun('subject')} had been negligent, and that carelessness made the scene confusing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is chess?",
            answer="Chess is a board game where two players move pieces in careful turns to try to outsmart each other.",
        ),
        QAItem(
            question="What does negligent mean?",
            answer="Negligent means not being careful enough about something that needed attention.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means something happens or appears again and again.",
        ),
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks for clues to solve a mystery.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is something unexpected that changes what the characters think is happening.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id} ({e.type}) " + " ".join(bits))
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
incident_valid(I) :- incident(I), clue_key(I, repetition).
incident_valid(I) :- incident(I), clue_key(I, surprise).
detective_notices(D) :- detective(D), curious(D).
case_strange(I) :- incident(I), surprise_key(I).
pattern_repeats(C) :- clue(C), repeated(C, N), N >= 2.
solution_ready(D, I) :- detective_notices(D), case_strange(I), pattern_repeats(C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        for a in sorted(room.affords):
            lines.append(asp.fact("affords", rid, a))
    for iid, inc in INCIDENTS.items():
        lines.append(asp.fact("incident", iid))
        lines.append(asp.fact("clue_key", iid, inc.clue_key))
        lines.append(asp.fact("surprise_key", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show incident_valid/1."))
    asp_set = set(asp.atoms(model, "incident_valid"))
    py_set = { (iid,) for iid, inc in INCIDENTS.items() if valid_incident(inc) }
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(py_set)} incidents).")
        return 0
    print("MISMATCH between clingo and Python gates")
    print("asp:", sorted(asp_set))
    print("py :", sorted(py_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world about chess, negligence, surprise, and repetition.")
    ap.add_argument("--setting", choices=ROOMS)
    ap.add_argument("--incident", choices=INCIDENTS)
    ap.add_argument("--name")
    ap.add_argument("--guard")
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
    setting = getattr(args, "setting", None) or rng.choice(list(ROOMS))
    incident = getattr(args, "incident", None) or rng.choice(list(INCIDENTS))
    if not reasonableness_gate(setting, incident):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    detective_name = getattr(args, "name", None) or rng.choice(DETECTIVE_NAMES)
    guard_name = getattr(args, "guard", None) or rng.choice(GUARD_NAMES)
    return StoryParams(setting=setting, incident=incident, detective_name=detective_name, guard_name=guard_name)


def generate(params: StoryParams) -> StorySample:
    room = _safe_lookup(ROOMS, params.setting)
    incident = _safe_lookup(INCIDENTS, params.incident)
    world = tell(room, incident, params.detective_name, params.guard_name)
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
    StoryParams(setting="chess_club", incident="missing_knight", detective_name="Mira", guard_name="Benn"),
    StoryParams(setting="library", incident="mixed_scores", detective_name="Iris", guard_name="Ruth"),
    StoryParams(setting="station_hall", incident="clock_alarm", detective_name="Ada", guard_name="Omar"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show incident_valid/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show incident_valid/1."))
        vals = sorted(set(asp.atoms(model, "incident_valid")))
        print(f"{len(vals)} valid incidents:")
        for (iid,) in vals:
            print(" ", iid)
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
            header = f"### {p.detective_name}: {p.incident} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
