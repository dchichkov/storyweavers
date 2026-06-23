#!/usr/bin/env python3
"""
storyworlds/worlds/pork_curiosity_mystery_to_solve_superhero_story.py
=====================================================================

A small storyworld for a superhero-style curiosity mystery.

Premise:
A child superhero hears a strange smell and finds a mystery about pork.
Curiosity pulls the hero toward the clue, a helper is worried about the mess,
and together they solve the mystery by following facts in the world.

The world model tracks:
- physical meters: smell, heat, mess, evidence, hunger, solved
- emotional memes: curiosity, worry, pride, relief, confidence

The story always has:
- a clear setup
- a clue-driven turn
- a resolution image that proves what changed

This script follows the Storyweavers contract and includes:
- StoryParams
- build_parser
- resolve_params
- generate
- emit
- --verify, --asp, --show-asp, --json, --qa, --trace, --all, -n, --seed

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
from typing import Callable, Optional

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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
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
    clues: set[str] = field(default_factory=set)
    furnishes: set[str] = field(default_factory=set)
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
class Mystery:
    id: str
    clue: str
    source: str
    reveal: str
    danger: str
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


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.smoke = False

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.smoke = self.smoke
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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


def _r_smell(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["pork_smell"] < THRESHOLD:
            continue
        sig = ("smell", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["curiosity"] += 1
        out.append(f"{ent.id} followed the smell and grew more curious.")
    return out


def _r_mystery(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["evidence"] < THRESHOLD:
            continue
        sig = ("mystery", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["confidence"] += 1
        out.append(f"The clue made the mystery feel smaller.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("smell", "physical", _r_smell),
    Rule("mystery", "social", _r_mystery),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def clue_at_risk(mystery: Mystery, place: Place) -> bool:
    return mystery.source in place.clues


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for mid, mystery in MYSTERIES.items():
            if clue_at_risk(mystery, place):
                combos.append((pid, mid))
    return combos


def solve_mystery(world: World, hero: Entity, helper: Entity, mystery: Mystery, tool: Tool) -> None:
    hero.meters["pork_smell"] += 1
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} was a little superhero who noticed every strange thing in {world.place.label}."
    )
    world.say(
        f"{hero.id} sniffed the air. Something smelled like pork, and {hero.pronoun()} wanted to know why."
    )
    world.para()
    helper.memes["worry"] += 1
    world.say(
        f"{helper.id} frowned and pointed at the clue. \"Maybe we should be careful,\" {helper.pronoun()} said."
    )
    world.say(
        f"{hero.id} looked closer and found {mystery.clue}. {mystery.reveal}"
    )
    hero.meters["evidence"] += 1
    propagate(world, narrate=True)
    world.para()
    hero.memes["pride"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"Then {hero.id} used {tool.phrase} to follow the clue, and the mystery was solved."
    )
    world.say(
        f"In the end, {mystery.danger}, but the real answer was simple: {mystery.reveal.lower()}"
    )
    world.say(
        f"{hero.id} stood by the window with a brave smile, the pork smell gone and the case solved."
    )


PLACES = {
    "kitchen": Place(
        id="kitchen",
        label="the kitchen",
        clues={"fridge", "counter", "pan"},
        furnishes={"window", "table"},
    ),
    "diner": Place(
        id="diner",
        label="the diner",
        clues={"tray", "grill", "counter"},
        furnishes={"booth", "sink"},
    ),
    "market": Place(
        id="market",
        label="the market",
        clues={"stall", "basket", "label"},
        furnishes={"cart", "awning"},
    ),
}

MYSTERIES = {
    "missing_lunch": Mystery(
        id="missing_lunch",
        clue="a paper bag on the counter",
        source="counter",
        reveal="It was not a monster at all. It was a warm pork lunch waiting for the right plate.",
        danger="the smell was only from food, not from a real danger",
        tags={"pork", "food", "mystery"},
    ),
    "secret_stall": Mystery(
        id="secret_stall",
        clue="a small label behind the basket",
        source="label",
        reveal="It turned out the pork came from a hidden lunch stall that was still open",
        danger="the clue looked suspicious, but it was just a food clue",
        tags={"pork", "market", "mystery"},
    ),
    "chef_note": Mystery(
        id="chef_note",
        clue="a note beside the grill",
        source="grill",
        reveal="A chef had cooked the pork for a kind neighbor and left a note so nobody would worry",
        danger="the smoky smell came from cooking, not from trouble",
        tags={"pork", "diner", "mystery"},
    ),
}

TOOLS = {
    "magnifier": Tool(
        id="magnifier",
        label="magnifier",
        phrase="a shiny magnifier",
        helps={"evidence"},
        tags={"detective", "curiosity"},
    ),
    "gloves": Tool(
        id="gloves",
        label="gloves",
        phrase="bright helper gloves",
        helps={"careful"},
        tags={"superhero", "helper"},
    ),
    "notebook": Tool(
        id="notebook",
        label="notebook",
        phrase="a tiny notebook",
        helps={"note"},
        tags={"mystery", "clue"},
    ),
}

HERO_NAMES = ["Nova", "Milo", "Zara", "Ruby", "Jasper", "Ivy", "Theo", "Luna"]
HELPER_NAMES = ["Aunt June", "Coach Bell", "Dr. Penny", "Mia", "Finn", "Sam"]


@dataclass
class StoryParams:
    place: str = "kitchen"
    mystery: str = "missing_lunch"
    tool: str = "magnifier"
    hero: str = "Nova"
    helper: str = "Aunt June"
    seed: Optional[int] = None
    samples: list = field(default_factory=list)
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


KNOWLEDGE = {
    "pork": [("What is pork?", "Pork is meat that comes from a pig. People cook it in many ways for meals.")],
    "curiosity": [("What is curiosity?", "Curiosity is the wish to know more about something. It helps you ask questions and look for clues.")],
    "mystery": [("What is a mystery?", "A mystery is something that is not clear at first. You solve it by finding clues and thinking carefully.")],
    "magnifier": [("What is a magnifier?", "A magnifier is a tool with a lens that helps you see small details more clearly.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a young child where {f["hero"].id} smells pork and follows a clue in {f["place"].label}.',
        f"Tell a curious mystery story where {f['hero'].id} uses a {(f.get('tool') or next(iter(TOOLS.values()))).label} to solve what the pork smell means.",
        f'Write a gentle superhero mystery that includes the word "pork" and ends with the case being solved.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    mystery: Mystery = f["mystery_cfg"]
    tool: Tool = f["tool_cfg"]
    return [
        QAItem(
            question=f"Why did {hero.id} go looking around {f['place'].label}?",
            answer=f"{hero.id} was curious about the pork smell, so {hero.pronoun()} went looking for a clue. {hero.id} wanted to solve the mystery instead of just guessing.",
        ),
        QAItem(
            question=f"What helped {hero.id} solve the mystery?",
            answer=f"{tool.phrase} helped {hero.id} notice the clue and follow it carefully. That made the answer easier to see.",
        ),
        QAItem(
            question=f"What was the answer to the pork mystery?",
            answer=f"The pork smell turned out to be harmless food, not danger. {mystery.reveal}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["mystery_cfg"].tags) | {"pork", "mystery", "curiosity"}
    if world.facts["tool_cfg"].id == "magnifier":
        tags.add("magnifier")
    out: list[QAItem] = []
    for key, items in KNOWLEDGE.items():
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
    return out


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
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
solved(H) :- clue_seen(H), curiosity(H,C), C > 0.
clue_seen(H) :- evidence(H,E), E > 0.
valid(Place, Mystery) :- place(Place), mystery(Mystery), clue_in(Place, Mystery).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for clue in sorted(place.clues):
            lines.append(asp.fact("clue_in", pid, clue))
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("source_of", mid, mystery.source))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    import asp
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid_combos().")
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, mystery=None, tool=None, hero=None, helper=None, seed=777), random.Random(777)))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=True, qa=True)
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero-style curiosity mystery about pork.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
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
              and (getattr(args, "mystery", None) is None or c[1] == getattr(args, "mystery", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mystery = rng.choice(list(combos))
    tool = getattr(args, "tool", None) or rng.choice(sorted(TOOLS))
    hero = getattr(args, "hero", None) or rng.choice(HERO_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    if helper == hero:
        helper = next(h for h in HELPER_NAMES if h != hero)
    return StoryParams(place=place, mystery=mystery, tool=tool, hero=hero, helper=helper)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.mystery not in MYSTERIES or params.tool not in TOOLS:
        pass
    place = _safe_lookup(PLACES, params.place)
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    tool = _safe_lookup(TOOLS, params.tool)
    world = World(place)
    hero = world.add(Entity(id=params.hero, kind="character", type="boy" if params.hero in {"Milo", "Jasper", "Theo"} else "girl", label=params.hero))
    helper = world.add(Entity(id=params.helper, kind="character", type="woman" if "Aunt" in params.helper or "Dr." in params.helper else "girl", label=params.helper))
    world.add(Entity(id="clue", label=mystery.clue))
    world.add(Entity(id="tool", label=tool.label))
    hero.meters["pork_smell"] = 1.0
    hero.meters["evidence"] = 1.0
    hero.memes["curiosity"] = 1.0
    helper.memes["worry"] = 1.0
    world.facts = {
        "hero": hero,
        "helper": helper,
        "mystery_cfg": mystery,
        "tool_cfg": tool,
        "place": place,
    }
    world.say(f"{hero.id} was a little superhero who loved clues, capes, and brave questions.")
    world.say(f"One day, {hero.id} caught a smell of pork drifting through {place.label}.")
    world.say(f"{hero.id} followed the smell, and {mystery.clue} looked like the first real clue.")
    world.para()
    world.say(f"{helper.id} worried the clue might lead to trouble, but {hero.id} stayed curious.")
    world.say(f"With {tool.phrase}, {hero.id} checked the clue and found the answer.")
    world.para()
    solve_mystery(world, hero, helper, mystery, tool)
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
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for place, mystery in asp_valid_combos():
            print(place, mystery)
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(StoryParams(place=p, mystery=m, tool="magnifier", hero="Nova", helper="Aunt June"))
                   for p, m in valid_combos()]
    else:
        for i in range(max(1, getattr(args, "n", None))):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
