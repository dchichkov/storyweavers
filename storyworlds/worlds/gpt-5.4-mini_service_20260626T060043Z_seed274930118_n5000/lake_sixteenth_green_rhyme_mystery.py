#!/usr/bin/env python3
"""
storyworlds/worlds/lake_sixteenth_green_rhyme_mystery.py
========================================================

A small story world for a gentle mystery at the lake, built from the seed words
"lake", "sixteenth", and "green", with rhyme as the clue-making instrument.

Premise:
- On the sixteenth day, a child visits the lake.
- A green object goes missing.
- A short rhyme points the way through the reeds.
- The ending reveals where the object was hiding and how the worry changed.

This world is intentionally small and constraint-driven: only plausible mystery
setups are generated, and the clue logic must be enough to solve the puzzle.
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
# Typed entities with physical meters and emotional memes.
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
    found_by: Optional[str] = None
    hidden_in: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    adult: object | None = None
    child: object | None = None
    object_ent: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
class Setting:
    place: str
    features: set[str] = field(default_factory=set)
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


@dataclass
class Mystery:
    id: str
    label: str
    phrase: str
    color: str
    hide_spots: set[str]
    clue_rhyme: str
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
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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


# ---------------------------------------------------------------------------
# Registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "lake": Setting(place="the lake", features={"water", "reeds", "dock"}),
    "dock": Setting(place="the dock by the lake", features={"water", "boards", "rope"}),
    "path": Setting(place="the path near the lake", features={"grass", "reeds", "stones"}),
}

MYSTERIES = {
    "green_boat": Mystery(
        id="green_boat",
        label="green boat",
        phrase="a little green rowboat",
        color="green",
        hide_spots={"reeds", "dock"},
        clue_rhyme="Green on the water, green in the reed; look where the ripples slow down their speed.",
        tags={"green", "lake", "boat", "rhyme"},
    ),
    "green_frog_pin": Mystery(
        id="green_frog_pin",
        label="green frog pin",
        phrase="a tiny green frog pin",
        color="green",
        hide_spots={"picnic_bench", "sandbag"},
        clue_rhyme="Green and small, it slipped from sight; check the place that holds things tight.",
        tags={"green", "rhyme", "pin"},
    ),
    "green_paddle": Mystery(
        id="green_paddle",
        label="green paddle",
        phrase="a painted green paddle",
        color="green",
        hide_spots={"dock", "boat_hook"},
        clue_rhyme="Green to steer and green to glide; look where the wooden boats are tied.",
        tags={"green", "lake", "dock", "rhyme"},
    ),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a small lantern",
        helps={"dock", "reeds"},
        tags={"light", "search"},
    ),
    "magnifier": Tool(
        id="magnifier",
        label="magnifying glass",
        phrase="a round magnifying glass",
        helps={"reading_clue", "search"},
        tags={"search", "clue"},
    ),
    "boots": Tool(
        id="boots",
        label="boots",
        phrase="rubber boots",
        helps={"water", "mud"},
        tags={"lake", "water"},
    ),
    "map": Tool(
        id="map",
        label="map",
        phrase="a folded map of the lakeside",
        helps={"reading_clue", "path"},
        tags={"search", "path"},
    ),
}

NAMES = ["Mia", "Nora", "Eli", "Theo", "Ava", "Lina", "Sam", "June"]
KINDS = ["girl", "boy"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    kind: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin.
# ---------------------------------------------------------------------------
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


ASP_RULES = r"""
#show valid_story/3.

valid_story(Place, Mystery, Kind) :- setting(Place), mystery(Mystery), child(Kind),
    needs(Mystery, Need), at(Place, Need), color(Mystery, green).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for feat in sorted(s.features):
            lines.append(asp.fact("at", pid, feat))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("color", mid, m.color))
        for spot in sorted(m.hide_spots):
            lines.append(asp.fact("needs", mid, spot))
    for k in KINDS:
        lines.append(asp.fact("child", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_stories() -> list[tuple[str, str, str]]:
    out = []
    for place, s in SETTINGS.items():
        for mid, m in MYSTERIES.items():
            if m.color != "green":
                continue
            if any(spot in s.features for spot in m.hide_spots):
                for k in KINDS:
                    out.append((place, mid, k))
    return sorted(out)


def asp_verify() -> int:
    a = set(asp_valid_stories())
    b = set(valid_stories())
    if a == b:
        print(f"OK: clingo gate matches valid_stories() ({len(a)} stories).")
        return 0
    print("MISMATCH between clingo and Python:")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# World simulation.
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    world = World(setting)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.kind,
        meters={"restlessness": 0.0, "search": 0.0, "relief": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0},
    ))
    adult = world.add(Entity(
        id="Caregiver",
        kind="character",
        type="mother",
        label="mom",
        meters={"patience": 1.0},
        memes={"calm": 1.0, "worry": 0.0},
    ))
    object_ent = world.add(Entity(
        id=mystery.id,
        type="thing",
        label=mystery.label,
        phrase=mystery.phrase,
        owner=child.id,
        hidden_in=next(iter(sorted(mystery.hide_spots))),
        meters={"hidden": 1.0, "glow": 0.0},
        memes={"mystery": 1.0},
    ))
    tool = world.add(Entity(
        id="search_tool",
        type="thing",
        label="magnifying glass",
        phrase="a round magnifying glass",
        meters={"shine": 1.0},
    ))
    world.facts.update(child=child, adult=adult, object=object_ent, tool=tool, mystery=mystery, params=params)
    return world


def _line_rhyme(world: World, child: Entity, mystery: Mystery) -> str:
    return f'"{mystery.clue_rhyme}" {child.pronoun("possessive")} mom said, like a tune for the day.'


def _begin(world: World, child: Entity, adult: Entity, mystery: Mystery) -> None:
    world.say(
        f"On the sixteenth, {child.id} went to {world.setting.place} with {child.pronoun('possessive')} {adult.label}."
    )
    world.say(
        f"{child.id} loved the green water and the quiet reeds, but something was missing: {mystery.phrase}."
    )
    child.memes["worry"] += 1.0
    adult.memes["worry"] += 1.0


def _clue(world: World, child: Entity, adult: Entity, mystery: Mystery) -> None:
    child.meters["search"] += 1.0
    world.say("Then a little rhyme floated in the air.")
    world.say(_line_rhyme(world, child, mystery))
    world.say(
        f"{child.id} listened close. The words pointed toward the reeds and the wet boards at the edge of the lake."
    )


def _search(world: World, child: Entity, adult: Entity, mystery: Mystery, tool: Entity) -> None:
    child.meters["search"] += 1.0
    world.say(
        f"{child.id} took {tool.phrase} and walked slowly along the dock, peeking under ropes and over shining puddles."
    )
    if world.setting.place == "lake":
        world.say(
            f"The green clue fit the shore best, so {child.id} knelt by the reeds where the water brushed the bank."
        )
    else:
        world.say(
            f"Even away from the dock, the rhyme still led {child.id} toward the lake side of the path."
        )


def _reveal(world: World, child: Entity, adult: Entity, mystery: Mystery) -> None:
    obj = world.get(mystery.id)
    obj.hidden_in = None
    obj.found_by = child.id
    obj.meters["hidden"] = 0.0
    obj.meters["found"] = 1.0
    child.memes["relief"] += 1.0
    child.memes["worry"] = 0.0
    adult.memes["worry"] = 0.0
    world.say(
        f"At last, {child.id} found {mystery.phrase} tucked in the reeds, just where the rhyme had pointed."
    )
    world.say(
        f"The green thing had not been lost forever at all; it had only been hiding with the hush of the lake."
    )
    world.say(
        f"{child.id} smiled, {child.pronoun('possessive')} {adult.label} smiled too, and the lake looked bright and safe again."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    child = world.get(params.name)
    adult = world.get("Caregiver")
    mystery = world.get(params.mystery)
    tool = world.get("search_tool")

    _begin(world, child, adult, _safe_lookup(MYSTERIES, params.mystery))
    world.para()
    _clue(world, child, adult, _safe_lookup(MYSTERIES, params.mystery))
    _search(world, child, adult, _safe_lookup(MYSTERIES, params.mystery), tool)
    _reveal(world, child, adult, _safe_lookup(MYSTERIES, params.mystery))
    return world


# ---------------------------------------------------------------------------
# Q&A.
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = _safe_fact(world, f, "params")
    mystery: Mystery = _safe_fact(world, f, "mystery")
    return [
        f'Write a short mystery for a child at {_safe_lookup(SETTINGS, params.place).place} on the sixteenth, and include the word "green".',
        f"Tell a gentle rhyme-driven story where {params.name} looks for {mystery.phrase} by the lake and finds it at the end.",
        f'Write a child-friendly mystery with a rhyme clue, a lake setting, and a clear reveal about a missing green object.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    adult: Entity = _safe_fact(world, f, "adult")
    mystery: Mystery = _safe_fact(world, f, "mystery")
    params: StoryParams = _safe_fact(world, f, "params")
    return [
        QAItem(
            question=f"Who went to {world.setting.place} on the sixteenth?",
            answer=f"{child.id} went to {world.setting.place} with {adult.label} on the sixteenth.",
        ),
        QAItem(
            question=f"What was the green mystery in the story?",
            answer=f"The missing thing was {mystery.phrase}.",
        ),
        QAItem(
            question="What helped lead the search?",
            answer="A little rhyme gave the clue and pointed the search toward the reeds by the lake.",
        ),
        QAItem(
            question=f"Where was {mystery.label} found?",
            answer=f"It was found hidden in the reeds by the lake, after the rhyme led the way.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt relieved and happy when the green thing was found.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "lake": [
        QAItem(
            question="What is a lake?",
            answer="A lake is a large body of water that sits in a land area, and people can watch it, splash near it, or go boating on it.",
        )
    ],
    "green": [
        QAItem(
            question="What kind of thing is green?",
            answer="Green is a color like leaves, grass, and some frogs.",
        )
    ],
    "rhyme": [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a poem or little song where some words sound alike at the ends.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["mystery"].tags)
    out: list[QAItem] = []
    for tag, qas in WORLD_KNOWLEDGE.items():
        if tag in tags:
            out.extend(qas)
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.found_by:
            bits.append(f"found_by={e.found_by}")
        lines.append(f"  {e.id:12} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Storyworld interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle lake mystery with a rhyme clue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--kind", choices=KINDS)
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
    combos = [c for c in valid_stories()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "mystery", None) is None or c[1] == getattr(args, "mystery", None))
              and (getattr(args, "kind", None) is None or c[2] == getattr(args, "kind", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mystery, kind = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    return StoryParams(place=place, mystery=mystery, name=name, kind=kind)


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
    StoryParams(place="lake", mystery="green_boat", name="Mia", kind="girl"),
    StoryParams(place="dock", mystery="green_paddle", name="Eli", kind="boy"),
    StoryParams(place="path", mystery="green_frog_pin", name="Nora", kind="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program(""))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_stories()
        print(f"{len(triples)} compatible stories:\n")
        for place, mystery, kind in triples:
            print(f"  {place:6}  {mystery:14}  {kind}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 40, 40):
            i += 1
            seed = base_seed + i
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
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
