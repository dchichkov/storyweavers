#!/usr/bin/env python3
"""
storyworlds/worlds/soggy_wasp_shotgun_mystery_to_solve_curiosity.py
====================================================================

A small standalone storyworld about a curious child, a soggy mystery, a wasp
problem, and an old shotgun that stays locked away. The tone leans ghost-story:
fog, creaks, lantern light, and a mystery that becomes a calm solution instead
of a scare.

The world is built from a tiny premise:

A child finds soggy footprints in an old house, hears a buzzing wasp sound, and
spots an old shotgun case in the hall. Curiosity pushes them to solve the
mystery. The turn comes when they learn the "ghostly" clues are from a leaky
roof, a wasp nest in the eaves, and a forgotten toolbox by the porch. The ending
proves what changed: the leak is patched, the wasps are left alone and handled
safely by a grown-up, and the child's curiosity becomes pride.

This file follows the Storyweavers contract:
- self-contained stdlib script
- eager shared results import
- lazy asp import inside ASP helpers
- StoryParams, registries, parser, resolve_params, generate, emit, main
- metrics over physical meters and emotional memes
- reasonableness gate plus inline ASP twin
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



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
            keys = [upper + "S", upper + "ES"]
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    locked: bool = False
    dangerous: bool = False
    wet: bool = False
    buzzing: bool = False

    adult: object | None = None
    case: object | None = None
    child: object | None = None
    eaves: object | None = None
    floor: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
        if not hasattr(self, "_tags"):
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
    gloomy: bool = False
    leaks: bool = False
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    kind: str
    wet: bool = False
    buzz: bool = False
    old: bool = False
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Problem:
    id: str
    label: str
    clue: str
    worry: str
    safe_fix: str
    solved_by: str
    risky: bool = False
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class StoryParams:
    place: str
    clue: str
    problem: str
    child_name: str
    child_gender: str
    guardian: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


PLACES = {
    "old_house": Place(id="old_house", label="the old house", gloomy=True, leaks=True,
                       affords={"mystery"}),
    "porch": Place(id="porch", label="the porch", gloomy=True, leaks=True,
                   affords={"mystery"}),
    "hall": Place(id="hall", label="the hallway", gloomy=True, leaks=True,
                  affords={"mystery"}),
}

CLUES = {
    "soggy_floor": Clue(id="soggy_floor", label="soggy footprints", kind="wet", wet=True),
    "wasp_sound": Clue(id="wasp_sound", label="a wasp buzz", kind="buzz", buzz=True),
    "shotgun_case": Clue(id="shotgun_case", label="an old shotgun case", kind="old", old=True),
}

PROBLEMS = {
    "leak": Problem(id="leak", label="a leaking roof", clue="soggy_floor",
                    worry="the floor looked haunted", safe_fix="patch the roof",
                    solved_by="bucket", risky=False),
    "wasps": Problem(id="wasps", label="wasps in the eaves", clue="wasp_sound",
                     worry="the buzzing sounded like a ghost song",
                     safe_fix="call a grown-up and keep away", solved_by="adult",
                     risky=True),
    "case": Problem(id="case", label="a locked shotgun case", clue="shotgun_case",
                    worry="the case looked spooky in the dark",
                    safe_fix="leave it locked and tell a grown-up",
                    solved_by="adult", risky=True),
}

GIRL_NAMES = ["Mina", "Ivy", "Rose", "Nora", "June"]
BOY_NAMES = ["Eli", "Theo", "Finn", "Miles", "Owen"]
TRAITS = ["curious", "careful", "brave", "quiet", "bright"]


class WorldView:
    pass


def _story_intro(world: World, child: Entity, guardian: Entity, clue: Clue, problem: Problem) -> None:
    child.memes["curiosity"] += 1
    child.memes["wonder"] += 1
    world.say(
        f"On a foggy evening, {child.id} wandered through {world.place.label} with "
        f"{child.pronoun('possessive')} {guardian.label_word}. The air felt damp, and "
        f"{clue.label} waited by the door like a secret."
    )
    world.say(
        f"{child.id} leaned closer. {child.pronoun().capitalize()} wanted to know why "
        f"the house felt so spooky, because {problem.worry}."
    )


def _r_soggy(world: World) -> list[str]:
    out = []
    if not world.place.leaks:
        return out
    for e in list(world.entities.values()):
        if e.id != "floor":
            continue
        sig = ("wet_floor", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.wet = True
        e.meters["wet"] = 1
        out.append("The floor was soggy from a hidden drip.")
    return out


def _r_wasp(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.id != "eaves":
            continue
        if e.meters.get("buzz", 0) >= THRESHOLD:
            sig = ("buzz", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            out.append("A wasp nest hummed in the dark rafters.")
    return out


CAUSAL_RULES = []


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(place: Place, clue: Clue, problem: Problem) -> bool:
    if clue.id == "shotgun_case" and not problem.risky:
        return False
    return True


def tell(place: Place, clue: Clue, problem: Problem, child_name: str = "Mina",
         child_gender: str = "girl", guardian: str = "grandma") -> World:
    world = World(place=place)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender))
    adult = world.add(Entity(id=guardian, kind="character", type="adult"))
    floor = world.add(Entity(id="floor", label="floor"))
    eaves = world.add(Entity(id="eaves", label="eaves"))
    case = world.add(Entity(id="case", label="shotgun case", locked=True, dangerous=True))

    _story_intro(world, child, adult, clue, problem)

    world.para()
    if clue.id == "soggy_floor":
        floor.meters["wet"] = 1
        world.say(
            f"{child.id} followed the damp prints and found that the hallway was soggy."
        )
        world.say(
            f"{child.pronoun().capitalize()} lifted {child.pronoun('possessive')} lamp and saw a drip from the roof."
        )
        child.memes["curiosity"] += 1
        adult.memes["calm"] += 1
        world.say(
            f"{adult.id} smiled and said the mystery was only a leak, not a ghost."
        )
        world.para()
        world.say(
            f"Together they set out a bucket and later patched the roof, so the floor could dry."
        )
        world.say(
            f"By morning, the scary puddles were gone, and {child.id} could walk through "
            f"{world.place.label} without leaving soggy prints."
        )
        solved = True
    elif clue.id == "wasp_sound":
        eaves.meters["buzz"] = 1
        world.say(
            f"{child.id} heard the buzzing and pointed up at the rafters, where a wasp nest hid."
        )
        world.say(
            f"{adult.id} said the wasps were not to be poked, because curious hands should stay safe."
        )
        child.memes["curiosity"] += 1
        adult.memes["care"] += 1
        world.para()
        world.say(
            f"They kept away, closed the door softly, and called for help. A grown-up later moved the nest."
        )
        world.say(
            f"The buzzing faded, and the house felt quiet again."
        )
        solved = True
    else:
        world.say(
            f"{child.id} found {clue.label} in the dim hall and stared at the locked case."
        )
        world.say(
            f"{adult.id} explained that the old shotgun was locked away and never for playing."
        )
        child.memes["curiosity"] += 1
        adult.memes["care"] += 1
        world.para()
        world.say(
            f"They left the case closed, searched for the real clue nearby, and found a wet trail from the porch."
        )
        world.say(
            f"The mystery turned into a simple answer: the house needed repairs, not fear."
        )
        solved = True

    world.facts.update(
        child=child, adult=adult, clue=clue, problem=problem, solved=solved,
        place=place, case=case, floor=floor, eaves=eaves
    )
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for c in CLUES:
            for prob in PROBLEMS:
                if reasonableness_gate(_safe_lookup(PLACES, p), _safe_lookup(CLUES, c), _safe_lookup(PROBLEMS, prob)):
                    combos.append((p, c, prob))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost-story style mystery for a young child about {f["clue"].label}, '
        f'where curiosity leads to a calm answer.',
        f"Tell a short spooky-but-safe story in {f['place'].label} with {f['clue'].label} "
        f"and a child named {f['child'].id}.",
        f'Write a gentle mystery that uses the words "soggy", "wasp", and "shotgun" '
        f'without making the shotgun part dangerous.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, adult, clue, problem = f["child"], f["adult"], f["clue"], f["problem"]
    place = f["place"].label
    return [
        QAItem(
            question=f"Why did {child.id} feel curious in {place}?",
            answer=(
                f"{child.id} felt curious because the house seemed spooky, and {clue.label} looked like a mystery. "
                f"{child.pronoun().capitalize()} wanted to understand what was really happening."
            ),
        ),
        QAItem(
            question=f"What was the real answer to the spooky clue?",
            answer=(
                f"The clue was not a ghost. It was really {problem.label}, which made the house seem strange until {adult.id} helped."
            ),
        ),
        QAItem(
            question=f"What did {adult.id} tell {child.id} about the shotgun case?",
            answer=(
                f"{adult.id} said the shotgun case had to stay locked and should never be treated like a toy. "
                f"That kept the mystery safe while they solved the rest of it."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does soggy mean?",
            answer="Soggy means wet and soft from too much water.",
        ),
        QAItem(
            question="Why should you stay away from wasps?",
            answer="Wasps can sting, so it is safer to leave them alone and get help from a grown-up.",
        ),
        QAItem(
            question="What should children do with a shotgun?",
            answer="Children should never play with a shotgun. It is a dangerous tool and must stay locked away with adults in charge.",
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
    lines.append("== (3) World knowledge ==")
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
        if e.locked:
            bits.append("locked=True")
        if e.dangerous:
            bits.append("dangerous=True")
        if e.wet:
            bits.append("wet=True")
        if e.buzzing:
            bits.append("buzzing=True")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,C,Pr) :- place(P), clue(C), problem(Pr), ok(P,C,Pr).
ok(P,C,Pr) :- place(P), clue(C), problem(Pr), not bad(C,Pr).
bad(shotgun_case, leak).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story mystery about soggy clues, wasps, and a locked shotgun case.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=["grandma", "grandpa", "mom", "dad"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "clue", None) is None or c[1] == getattr(args, "clue", None))
              and (getattr(args, "problem", None) is None or c[2] == getattr(args, "problem", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, clue, problem = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guardian = getattr(args, "guardian", None) or rng.choice(["grandma", "grandpa", "mom", "dad"])
    return StoryParams(place=place, clue=clue, problem=problem, child_name=name,
                       child_gender=gender, guardian=guardian)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(CLUES, params.clue), _safe_lookup(PROBLEMS, params.problem),
                 params.child_name, params.child_gender, params.guardian)
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
    StoryParams(place="old_house", clue="soggy_floor", problem="leak", child_name="Mina", child_gender="girl", guardian="grandma"),
    StoryParams(place="hall", clue="wasp_sound", problem="wasps", child_name="Eli", child_gender="boy", guardian="dad"),
    StoryParams(place="porch", clue="shotgun_case", problem="case", child_name="Nora", child_gender="girl", guardian="grandpa"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("\n".join(map(str, asp_valid_combos())))
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
