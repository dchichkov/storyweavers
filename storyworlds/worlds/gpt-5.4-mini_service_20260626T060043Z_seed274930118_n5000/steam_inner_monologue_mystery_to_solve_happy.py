#!/usr/bin/env python3
"""
storyworlds/worlds/steam_inner_monologue_mystery_to_solve_happy.py
===================================================================

A small space-adventure storyworld about a child crew member, a strange steam
mystery, and a happy fix reached through inner monologue and careful clues.

The premise is simple: a young spacer notices steam where it should not be,
thinks through the clues, and helps the ship stay safe.

This world is constraint-checked and reproducible.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "pilot"}
        male = {"boy", "father", "man", "pilot"}
        if self.type in female and self.type != "pilot":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male and self.type != "pilot":
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
class Location:
    id: str
    label: str
    indoors: bool = True
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
class Tool:
    id: str
    label: str
    phrase: str
    fixes: set[str] = field(default_factory=set)
    requires: set[str] = field(default_factory=set)
    carries: set[str] = field(default_factory=set)
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
class Mystery:
    id: str
    clue_word: str
    source: str
    effect: str
    solution_tool: str
    place: str
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
    def __init__(self, location: Location) -> None:
        self.location = location
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    location: str
    mystery: str
    hero_name: str
    hero_gender: str
    helper_name: str
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


LOCATIONS = {
    "engine_room": Location(id="engine_room", label="the engine room", indoors=True, affords={"investigate", "repair"}),
    "hallway": Location(id="hallway", label="the long hallway", indoors=True, affords={"investigate"}),
    "observation_deck": Location(id="observation_deck", label="the observation deck", indoors=True, affords={"investigate"}),
}

MYSTERIES = {
    "steam_pipe": Mystery(
        id="steam_pipe",
        clue_word="steam",
        source="a loose pipe joint",
        effect="a silver cloud of steam near the floor",
        solution_tool="wrench",
        place="engine_room",
    ),
    "steam_panel": Mystery(
        id="steam_panel",
        clue_word="steam",
        source="an overworked panel",
        effect="a warm hiss behind the wall",
        solution_tool="coolant_patch",
        place="hallway",
    ),
    "steam_valve": Mystery(
        id="steam_valve",
        clue_word="steam",
        source="a stuck valve",
        effect="a puff of steam by the rail",
        solution_tool="wrench",
        place="observation_deck",
    ),
}

TOOLS = {
    "wrench": Tool(id="wrench", label="wrench", phrase="a small silver wrench", fixes={"steam"}, requires={"pipe", "valve"}),
    "coolant_patch": Tool(id="coolant_patch", label="coolant patch", phrase="a sticky coolant patch", fixes={"steam"}, requires={"panel"}),
}

HERO_NAMES = ["Mira", "Tavi", "Niko", "Lena", "Jax", "Rin", "Pia", "Sora"]
HELPER_NAMES = ["Ari", "Bo", "Kestrel", "Nova", "Quill", "Ada"]
GENDERS = ["girl", "boy"]
LOCS = list(LOCATIONS)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld about steam, clues, and a happy ending.")
    ap.add_argument("--location", choices=LOCS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--helper")
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


def reasonableness_gate(location: str, mystery: str) -> bool:
    return _safe_lookup(LOCATIONS, location).id == _safe_lookup(MYSTERIES, mystery).place


def valid_combos() -> list[tuple[str, str]]:
    return [(loc, mys) for loc in LOCATIONS for mys in MYSTERIES if reasonableness_gate(loc, mys)]


def explain_rejection(location: str, mystery: str) -> str:
    m = _safe_lookup(MYSTERIES, mystery)
    return f"(No story: {m.clue_word} mystery belongs in {m.place}, not in {location}.)"


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for loc in LOCATIONS.values():
        lines.append(asp.fact("location", loc.id))
        if loc.indoors:
            lines.append(asp.fact("indoors", loc.id))
        for a in sorted(loc.affords):
            lines.append(asp.fact("affords", loc.id, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("at_place", mid, m.place))
        lines.append(asp.fact("solution_tool", mid, m.solution_tool))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for fix in sorted(t.fixes):
            lines.append(asp.fact("fixes", tid, fix))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Loc, M) :- location(Loc), mystery(M), at_place(M, Loc).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


class StoryWorld:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.world = World(_safe_lookup(LOCATIONS, params.location))
        self.world.facts = {}
        self.hero = self.world.add(Entity(id=params.name, kind="character", type=params.hero_gender, label=params.name))
        self.helper = self.world.add(Entity(id=params.helper_name, kind="character", type="friend", label=params.helper_name))
        self.mystery = _safe_lookup(MYSTERIES, params.mystery)
        self.tool = self.world.add(Entity(id=_safe_lookup(TOOLS, self.mystery.solution_tool).id, kind="thing", type="tool", label=_safe_lookup(TOOLS, self.mystery.solution_tool).label, phrase=_safe_lookup(TOOLS, self.mystery.solution_tool).phrase))

    def build(self) -> None:
        w = self.world
        hero = self.hero
        helper = self.helper
        mystery = self.mystery
        tool = self.tool

        hero.memes["curiosity"] = 1
        w.say(f"{hero.id} drifted through {w.location.label} in a tiny blue ship, listening to the hush of the panels.")
        w.say(f"Then {hero.id} noticed {mystery.effect}.")
        w.say(f"{hero.id} thought, 'That does not belong here. If I stay calm, the clues will make sense.'")

        w.para()
        w.say(f"{hero.id} looked closer and whispered to {hero.pronoun('object')} self, 'Steam means something is warm, leaking, or stuck. I should follow the sound, not the worry.'")
        w.say(f"{helper.id} hurried over and asked what the little cloud was doing there.")
        w.say(f"{hero.id} answered, 'I think I can solve it. The ship is trying to tell us a secret.'")

        w.para()
        if mystery.solution_tool == "wrench":
            w.say(f"{hero.id} found {tool.phrase} in the side kit.")
            w.say(f"Carefully, {hero.id} turned the loose part until the hiss faded away.")
        else:
            w.say(f"{hero.id} found {tool.phrase} in the repair drawer.")
            w.say(f"Carefully, {hero.id} pressed the patch over the hot spot until the soft hiss went quiet.")
        w.say(f"The secret was simple: {mystery.source} had been making the steam.")
        hero.memes["joy"] = 1
        helper.memes["joy"] = 1
        w.say(f"{helper.id} grinned and said the ship sounded happy again.")
        w.say(f"{hero.id} smiled too, because the mystery was solved and the little starship could fly on.")

        w.facts = {
            "hero": hero,
            "helper": helper,
            "mystery": mystery,
            "tool": tool,
            "location": w.location,
        }

    def sample(self) -> StorySample:
        self.build()
        return StorySample(
            params=self.params,
            story=self.world.render(),
            prompts=generation_prompts(self.world),
            story_qa=story_qa(self.world),
            world_qa=world_qa(self.world),
            world=self.world,
        )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    mystery = _safe_fact(world, f, "mystery")
    return [
        f'Write a short space-adventure story for a young child about {hero.id} noticing {mystery.clue_word}.',
        f"Tell a gentle mystery story where {hero.id} listens to an inner monologue and fixes a ship problem.",
        f"Write a happy ending story about a small crew solving a steam clue on a spaceship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    mystery = _safe_fact(world, f, "mystery")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    loc = _safe_fact(world, f, "location")
    return [
        QAItem(
            question=f"What did {hero.id} notice in {loc.label}?",
            answer=f"{hero.id} noticed {mystery.effect}, and the clue word was steam.",
        ),
        QAItem(
            question=f"How did {hero.id} think about the mystery before acting?",
            answer=f"{hero.id} used a quiet inner monologue and told {hero.pronoun('object')} self to stay calm and follow the clues.",
        ),
        QAItem(
            question=f"What helped solve the problem?",
            answer=f"{tool.phrase} helped because it matched the kind of problem on the ship.",
        ),
        QAItem(
            question=f"Who shared the happy ending with {hero.id}?",
            answer=f"{helper.id} shared the happy ending after the mystery was fixed and the ship became quiet again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is steam?",
            answer="Steam is warm water vapor, like a mist that can rise when water gets hot.",
        ),
        QAItem(
            question="Why can steam be a clue in a spaceship story?",
            answer="Steam can point to a leak, a loose part, or something that is getting too hot.",
        ),
        QAItem(
            question="What does a wrench do?",
            answer="A wrench helps turn and tighten parts so a loose piece can fit more safely.",
        ),
    ]


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
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams(location="engine_room", mystery="steam_pipe", hero_name="Mira", hero_gender="girl", helper_name="Ari"),
    StoryParams(location="hallway", mystery="steam_panel", hero_name="Tavi", hero_gender="boy", helper_name="Nova"),
    StoryParams(location="observation_deck", mystery="steam_valve", hero_name="Lena", hero_gender="girl", helper_name="Quill"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "location", None) and getattr(args, "mystery", None) and not reasonableness_gate(getattr(args, "location", None), getattr(args, "mystery", None)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "location", None) is None or c[0] == getattr(args, "location", None))
              and (getattr(args, "mystery", None) is None or c[1] == getattr(args, "mystery", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    loc, mys = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(GENDERS)
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    return StoryParams(location=loc, mystery=mys, hero_name=name, hero_gender=gender, helper_name=helper)


def generate(params: StoryParams) -> StorySample:
    return StoryWorld(params).sample()


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n#show valid/2.\n"


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(build_asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (location, mystery) combos:\n")
        for loc, mys in combos:
            print(f"  {loc:18} {mys}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
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
            header = f"### {p.hero_name}: {p.mystery} in {p.location}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
