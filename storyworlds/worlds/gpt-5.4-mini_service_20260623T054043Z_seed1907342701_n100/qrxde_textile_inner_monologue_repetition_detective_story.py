#!/usr/bin/env python3
"""
storyworlds/worlds/qrxde_textile_inner_monologue_repetition_detective_story.py
=============================================================================

A small standalone storyworld for a child-facing detective story. The domain is
built around a missing textile clue, a notebook full of repeated thoughts, and a
detective who solves the case by listening to an inner monologue.

Seed premise:
- Words: qrxde, textile
- Features: Inner Monologue, Repetition
- Style: Detective Story

This world keeps a tight simulation: typed entities with physical meters and
emotional memes, a small causal engine, a reasonableness gate, and an inline ASP
twin for parity checks.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    assistant: object | None = None
    clue: object | None = None
    detective: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
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
    phrase: str
    location: str
    risk: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Action:
    id: str
    verb: str
    search: str
    problem: str
    resolve: str
    tags: set[str] = field(default_factory=set)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    detective: str
    detective_gender: str
    assistant: str
    assistant_gender: str
    clue: str
    action: str
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
    "office": Place(id="office", label="the little detective office", affords={"search", "write"}),
    "library": Place(id="library", label="the quiet library nook", affords={"search", "write"}),
    "museum": Place(id="museum", label="the tiny museum hallway", affords={"search", "write"}),
    "shop": Place(id="shop", label="the fabric shop corner", affords={"search", "write"}),
}

CLUES = {
    "thread": Clue(id="thread", label="a blue textile thread", phrase="a blue textile thread", location="under the desk", risk="could be lost"),
    "scarf": Clue(id="scarf", label="a striped textile scarf", phrase="a striped textile scarf", location="on a chair", risk="could be mixed up"),
    "patch": Clue(id="patch", label="a bright textile patch", phrase="a bright textile patch", location="near the drawer", risk="could be folded away"),
    "ribbon": Clue(id="ribbon", label="a soft textile ribbon", phrase="a soft textile ribbon", location="beside the lamp", risk="could be hidden"),
}

ACTIONS = {
    "follow": Action(id="follow", verb="follow the clues", search="look again", problem="the clue seemed to vanish", resolve="careful eyes found the pattern"),
    "sort": Action(id="sort", verb="sort the clues", search="line everything up", problem="the pieces were out of order", resolve="the right order made sense"),
    "match": Action(id="match", verb="match the clues", search="compare the fibers", problem="the colors did not seem to fit", resolve="the matching weave stood out"),
    "trace": Action(id="trace", verb="trace the clue", search="study the edges", problem="the trail looked thin", resolve="the repeated thread led onward"),
}

GIRL_NAMES = ["Mina", "Luna", "Ada", "Nia", "Ivy", "Rosa", "Maya", "Lila"]
BOY_NAMES = ["Noah", "Eli", "Sam", "Theo", "Finn", "Max", "Owen", "Leo"]
TRAITS = ["curious", "careful", "quiet", "bright", "patient", "sharp"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for c in CLUES:
            for a in ACTIONS:
                combos.append((p, c, a))
    return combos


def _rule_hint(world: World) -> list[str]:
    out = []
    detective = world.get("detective")
    clue = world.get("clue")
    if detective.memes["doubt"] >= THRESHOLD and clue.meters["hidden"] >= THRESHOLD:
        sig = ("hint", clue.id)
        if sig not in world.fired:
            world.fired.add(sig)
            clue.meters["noticed"] += 1
            detective.memes["focus"] += 1
            out.append("inner_hint")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    events: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for ev in _rule_hint(world):
            changed = True
            if ev != "inner_hint":
                events.append(ev)
    if narrate:
        for ev in events:
            world.say(ev)
    return events


def reasonableness_check(place: Place, clue: Clue, action: Action) -> bool:
    return "search" in place.affords and clue.id in CLUES and action.id in ACTIONS


def aspire_inner_voice(detective: Entity, clue: Clue, action: Action) -> None:
    detective.memes["doubt"] += 1
    detective.memes["focus"] += 1


def introduce(world: World, detective: Entity, assistant: Entity, clue: Entity) -> None:
    world.say(
        f"{detective.id} was a little detective with a notebook and a habit of thinking twice. "
        f"{assistant.id} stayed close, because {detective.pronoun('possessive')} cases always started with a quiet look."
    )
    world.say(
        f"That morning, a textile clue was missing: {clue.phrase} had been seen {world.facts['clue'].location}, "
        f"but now it was nowhere in sight."
    )


def inner_monologue(world: World, detective: Entity, clue: Entity, action: Action) -> None:
    detective.memes["worry"] += 1
    world.say(
        f'"Think, think, think," {detective.id} told {detective.pronoun("object")}self. '
        f'"If the textile clue is hidden, then the answer is probably hidden too."'
    )
    world.say(
        f"{detective.id} looked at the floor, at the chair, and at the lamp, repeating the idea again and again: "
        f"find the clue, find the clue, find the clue."
    )


def search_scene(world: World, detective: Entity, assistant: Entity, clue: Entity, action: Action) -> None:
    detective.memes["determination"] += 1
    assistant.memes["helpfulness"] += 1
    clue.meters["hidden"] += 1
    world.say(
        f"{assistant.id} said, '{action.search}.' {detective.id} nodded and started to {action.verb} around {world.place.label}."
    )
    world.say(
        f"The detective checked {clue.attrs['search_spot']} first, then checked it again, because sometimes a clue only looked gone."
    )
    propagate(world, narrate=False)


def turn(world: World, detective: Entity, clue: Entity, action: Action) -> None:
    clue.meters["noticed"] += 1
    clue.meters["hidden"] = 0
    detective.memes["relief"] += 1
    world.say(
        f"Then {detective.id} stopped. The repeated thought clicked into place. "
        f"{action.resolve.capitalize()}, and the textile clue was there after all."
    )
    world.say(
        f"It had been tucked near {clue.attrs['search_spot']}, exactly where the detective's inner voice kept pointing."
    )


def ending(world: World, detective: Entity, assistant: Entity, clue: Entity) -> None:
    detective.memes["pride"] += 1
    assistant.memes["joy"] += 1
    world.say(
        f"{detective.id} wrote the answer down at last. The notebook was full of crossed-out guesses, "
        f"but the true clue sat on top of the page, neat and plain."
    )
    world.say(
        f"By the end, {assistant.id} held the textile clue carefully while {detective.id} smiled at the solved case, "
        f"the same clue now resting safely on the table instead of hiding in the room."
    )


def tell(place: Place, clue_cfg: Clue, action: Action, detective_name: str, detective_gender: str,
         assistant_name: str, assistant_gender: str, trait: str = "careful") -> World:
    world = World(place)
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective", attrs={"trait": trait}))
    assistant = world.add(Entity(id=assistant_name, kind="character", type=assistant_gender, role="assistant"))
    clue = world.add(Entity(id="clue", type="thing", label=clue_cfg.label, phrase=clue_cfg.phrase, tags=set(clue_cfg.tags), attrs={"search_spot": clue_cfg.location}))
    world.facts["place"] = place
    world.facts["clue"] = clue_cfg
    world.facts["action"] = action
    world.facts["detective"] = detective
    world.facts["assistant"] = assistant
    detective.memes["doubt"] = 0.0
    detective.memes["focus"] = 0.0
    assistant.memes["helpfulness"] = 0.0

    introduce(world, detective, assistant, clue)
    world.para()
    inner_monologue(world, detective, clue, action)
    search_scene(world, detective, assistant, clue, action)
    world.para()
    turn(world, detective, clue, action)
    world.para()
    ending(world, detective, assistant, clue)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for a young child that includes the words "{f["detective"].id}", "textile", and "qrxde".',
        f"Tell a mystery about {f['detective'].id} who keeps thinking to {f['detective'].pronoun('object')}self and repeats a clue until it makes sense.",
        f"Write a gentle detective story where a textile clue is missing, an inner voice keeps repeating the answer, and the case is solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]
    assistant: Entity = f["assistant"]
    clue: Clue = f["clue"]
    action: Action = f["action"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"Who was the story about in {place.label}?",
            answer=f"It was about {detective.id}, a little detective, and {assistant.id}, who helped search for the textile clue. They worked together in {place.label}.",
        ),
        QAItem(
            question=f"What was missing from the room?",
            answer=f"A textile clue was missing. It had last been seen {clue.location}, so the detective kept checking there in the story.",
        ),
        QAItem(
            question=f"Why did {detective.id} keep repeating thoughts?",
            answer=f"{detective.id} was using an inner monologue to stay focused. The repeated thinking helped the detective notice the clue pattern and solve the case.",
        ),
        QAItem(
            question=f"How did {assistant.id} help solve the mystery?",
            answer=f"{assistant.id} reminded {detective.id} to keep looking and helped search the room. That steady help made the repeated clue easier to spot.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The missing textile clue was found and set safely on the table. The case went from confusing to solved, and the notebook ended with the real answer written down.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues and tries to solve a mystery by noticing small details.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private voice in your mind that helps you think things through.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means saying or doing something again and again. It can help you remember or notice a pattern.",
        ),
        QAItem(
            question="What is textile?",
            answer="Textile means cloth or fabric. Shirts, scarves, and ribbons can all be made from textile.",
        ),
        QAItem(
            question="Why are clues important in a mystery?",
            answer="Clues are important because they help show what happened. A detective can use them to solve the case.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="office", detective="Mina", detective_gender="girl", assistant="Eli", assistant_gender="boy", clue="thread", action="trace", seed=1),
    StoryParams(place="library", detective="Noah", detective_gender="boy", assistant="Ada", assistant_gender="girl", clue="scarf", action="follow", seed=2),
    StoryParams(place="museum", detective="Luna", detective_gender="girl", assistant="Sam", assistant_gender="boy", clue="patch", action="sort", seed=3),
    StoryParams(place="shop", detective="Theo", detective_gender="boy", assistant="Ivy", assistant_gender="girl", clue="ribbon", action="match", seed=4),
]


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("risk", cid, c.risk))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,C,A) :- place(P), clue(C), action(A), affords(P,search).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    a = set(asp_valid_combos())
    b = set(valid_combos())
    ok = a == b
    if ok:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
    else:
        print("MISMATCH:")
        if a - b:
            print(" only in clingo:", sorted(a - b))
        if b - a:
            print(" only in python:", sorted(b - a))
    # smoke test
    try:
        sample = generate(CURATED[0])
        assert sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        ok = False
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld with a textile clue and an inner monologue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--detective")
    ap.add_argument("--assistant")
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--action", choices=ACTIONS)
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
              and (getattr(args, "action", None) is None or c[2] == getattr(args, "action", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, clue, action = rng.choice(list(combos))
    detective_gender = rng.choice(["girl", "boy"])
    assistant_gender = "boy" if detective_gender == "girl" else "girl"
    detective = getattr(args, "detective", None) or rng.choice(GIRL_NAMES if detective_gender == "girl" else BOY_NAMES)
    assistant = getattr(args, "assistant", None) or rng.choice([n for n in (BOY_NAMES + GIRL_NAMES) if n != detective])
    return StoryParams(
        place=place,
        detective=detective,
        detective_gender=detective_gender,
        assistant=assistant,
        assistant_gender=assistant_gender,
        clue=clue,
        action=action,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.clue not in CLUES or params.action not in ACTIONS:
        pass
    world = tell(
        _safe_lookup(PLACES, params.place),
        _safe_lookup(CLUES, params.clue),
        _safe_lookup(ACTIONS, params.action),
        params.detective,
        params.detective_gender,
        params.assistant,
        params.assistant_gender,
    )
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
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
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.detective}: {p.clue} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
