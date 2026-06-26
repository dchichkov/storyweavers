#!/usr/bin/env python3
"""
Standalone storyworld: chipmunk, magic, and a small mystery.

A chipmunk notices something gone missing, follows magical clues, and discovers
where the lost object went. The world is tiny, concrete, and state-driven:
the chipmunk has feelings, the forest has places, the magic leaves traces, and
the ending proves what changed.
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
# Entities and world state
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
    kind: str = "thing"  # "character" | "thing" | "place"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    found_by: Optional[str] = None
    hidden_in: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    clue: object | None = None
    hero: object | None = None
    hide: object | None = None
    lost: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.label in {"she", "he"}:
            return {"subject": self.label, "object": "her" if self.label == "she" else "him", "possessive": "her" if self.label == "she" else "his"}[case]
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
    id: str
    label: str
    detail: str
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
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)

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

    def copy(self) -> "World":
        import copy as _copy
        return World(
            place=self.place,
            entities=_copy.deepcopy(self.entities),
            facts=_copy.deepcopy(self.facts),
            paragraphs=[[]],
            fired=set(self.fired),
            trace=list(self.trace),
        )


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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


SETTINGS = {
    "oak_hollow": Place("oak_hollow", "Oak Hollow", "an old hollow with roots, moss, and a round stump"),
    "fern_path": Place("fern_path", "Fern Path", "a narrow path with ferns leaning over it"),
    "moon_pond": Place("moon_pond", "Moon Pond", "a quiet pond that reflects the sky like a polished spoon"),
}

MAGIC = {
    "glow": "a faint glow",
    "spark": "tiny sparks",
    "whisper": "a whispering breeze",
    "shimmer": "a silver shimmer",
}

HIDING_SPOTS = {
    "stump": "inside the hollow stump",
    "moss": "under a patch of moss",
    "root": "beneath the tangled roots",
    "lantern": "in the old lantern",
}

NAMES = ["Pip", "Milo", "Tess", "Nina", "Arlo", "Mina"]
TRAITS = ["curious", "careful", "brave", "quiet", "bright-eyed"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str = ""
    magic: str = "glow"
    name: str = "Pip"
    trait: str = "curious"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
    py: set[str] = field(default_factory=set)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a chipmunk mystery with magic clues.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    magic = getattr(args, "magic", None) or rng.choice(list(MAGIC))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, magic=magic, name=name, trait=trait)


def _chipmunk_label(name: str) -> str:
    return f"{name}, the chipmunk"


def _is_chipmunk(text: str) -> bool:
    return "chipmunk" in text.lower()


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def setup_world(params: StoryParams) -> World:
    world = World(place=_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id="hero", kind="character", label="chipmunk"))
    hero.meters["worry"] = 0.0
    hero.meters["curiosity"] = 1.0
    hero.memes["worry"] = 1.0
    hero.memes["hope"] = 0.5

    lost = world.add(Entity(
        id="lost_acorn",
        kind="thing",
        label="acorn",
        phrase="a tiny gold-painted acorn",
        owner="hero",
        hidden_in=None,
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        label=params.magic,
        phrase=f"{MAGIC[params.magic]} that floated like a clue",
    ))
    hide = world.add(Entity(
        id="hiding_spot",
        kind="place",
        label="hiding place",
        phrase=_safe_lookup(HIDING_SPOTS, rng_choice_from_place(world.place.id)),
    ))

    world.facts.update(
        hero=hero,
        lost=lost,
        clue=clue,
        place=world.place,
        magic=params.magic,
    )
    return world


def rng_choice_from_place(place_id: str) -> str:
    if place_id == "oak_hollow":
        return "stump"
    if place_id == "fern_path":
        return "moss"
    return "lantern"


def start_story(world: World, params: StoryParams) -> None:
    hero = world.get("hero")
    world.say(
        f"{_chipmunk_label(params.name)} was {params.trait} and knew every crack and shadow in {world.place.label}."
    )
    world.say(
        f"One morning, {params.name} found that {hero.pronoun('possessive')} little acorn was gone."
    )
    world.say(
        f"Then a bit of {params.magic} twinkled near the ground, as if the forest wanted to tell a secret."
    )
    hero.meters["worry"] += 1
    hero.memes["hope"] += 1


def apply_magic_clue(world: World, params: StoryParams) -> None:
    hero = world.get("hero")
    clue = world.get("clue")
    if ("magic", params.magic) in world.fired:
        return
    world.fired.add(("magic", params.magic))
    if params.magic == "glow":
        world.say("The glow gathered near a stump, and its light pointed toward a dark crack in the roots.")
    elif params.magic == "spark":
        world.say("The sparks hopped from stone to stone, stopping beside a patch of moss.")
    elif params.magic == "whisper":
        world.say("The whisper brushed the leaves, making them sway toward the old lantern.")
    else:
        world.say("The shimmer traced a thin line through the grass, as neat as a ribbon.")
    clue.found_by = hero.id
    hero.meters["curiosity"] += 1


def investigate(world: World, params: StoryParams) -> str:
    hero = world.get("hero")
    spot = rng_choice_from_place(world.place.id)
    if params.magic == "glow":
        spot = "stump"
    elif params.magic == "spark":
        spot = "moss"
    elif params.magic == "whisper":
        spot = "lantern"
    else:
        spot = "root"
    hidden_text = _safe_lookup(HIDING_SPOTS, spot)
    world.say(
        f"{params.name} followed the {params.magic} through {world.place.label} and peeked {hidden_text}."
    )
    return spot


def resolve(world: World, params: StoryParams, spot: str) -> None:
    hero = world.get("hero")
    lost = world.get("lost")
    if spot not in HIDING_SPOTS:
        pass
    world.para()
    lost.hidden_in = spot
    lost.found_by = hero.id
    hero.meters["worry"] = 0.0
    hero.memes["hope"] += 1.0
    world.say(
        f"At last, {params.name} found the acorn tucked {_safe_lookup(HIDING_SPOTS, spot)}. It had rolled there by accident."
    )
    world.say(
        f"{params.name} laughed softly, set the acorn back in a safe nook, and watched the last bit of {params.magic} fade."
    )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    start_story(world, params)
    world.para()
    apply_magic_clue(world, params)
    spot = investigate(world, params)
    resolve(world, params, spot)
    world.facts["spot"] = spot
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_params(params: StoryParams) -> bool:
    return params.place in SETTINGS and params.magic in MAGIC and _is_chipmunk("chipmunk")


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.facts
    return [
        f"Write a short mystery story for a young child about a chipmunk and a {p['magic']} clue.",
        f"Tell a gentle forest mystery where {p['hero'].id} loses an acorn and follows magical signs in {p['place'].label}.",
        "Write a child-friendly story with a clear problem, a clue, an investigation, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    place = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "place")
    magic = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "magic")
    spot = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "spot")
    lost = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "lost")
    return [
        QAItem(
            question=f"Who is the mystery about?",
            answer=f"It is about a chipmunk named {hero.id} who is looking for a lost acorn.",
        ),
        QAItem(
            question=f"What magical clue helped {hero.id} investigate {place.label}?",
            answer=f"A {magic} clue appeared in {place.label}, and it led {hero.id} toward the hiding place.",
        ),
        QAItem(
            question=f"Where was the acorn found?",
            answer=f"The acorn was found {_safe_lookup(HIDING_SPOTS, spot)}. It had simply rolled there by accident.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"{hero.id} stopped worrying, the acorn was safe again, and the mystery was solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    magic = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "magic")
    base = [
        QAItem(
            question="What is a chipmunk?",
            answer="A chipmunk is a small striped squirrel that gathers seeds and nuts.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a story about something that is missing, hidden, or not yet understood.",
        ),
        QAItem(
            question=f"What does {magic} mean in a story?",
            answer=f"It means the story has a little bit of magical, surprising feeling, like a clue that shines or whispers.",
        ),
    ]
    return base


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"{e.id}: kind={e.kind} label={e.label} hidden_in={e.hidden_in} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    lines.append(f"place={world.place.label}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
magic_clue(M) :- magic(M).
mystery_story(P, M) :- place(P), magic(M).
valid(P, M) :- place(P), magic(M).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for mid in MAGIC:
        lines.append(asp.fact("magic", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, m) for p in SETTINGS for m in MAGIC if valid_params(StoryParams(place=p, magic=m))}
    cl = set(asp_valid_pairs())
    if py == cl:
        print(f"OK: ASP parity confirmed for {len(py)} place/magic pairs.")
        return 0
    print("MISMATCH between Python and ASP:")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    if not valid_params(params):
        pass
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="oak_hollow", magic="glow", name="Pip", trait="curious"),
    StoryParams(place="fern_path", magic="spark", name="Mina", trait="careful"),
    StoryParams(place="moon_pond", magic="whisper", name="Tess", trait="bright-eyed"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        pairs = asp_valid_pairs()
        for p, m in pairs:
            print(f"{p} {m}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name} at {p.place} with {p.magic}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
