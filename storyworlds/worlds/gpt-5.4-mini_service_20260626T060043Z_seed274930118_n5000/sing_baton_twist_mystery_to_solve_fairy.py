#!/usr/bin/env python3
"""
A small fairy-tale storyworld about a song, a baton, and a mystery to solve.

The world model keeps track of physical meters and emotional memes:
- meters: where objects are, what they can do, what gets moved or revealed
- memes: curiosity, worry, hope, joy, and relief

A typical tale:
- A young fairy wants to sing with a special baton.
- A strange sound or missing note creates a mystery.
- The fairy follows clues, makes a gentle twist in the plan, and solves it.
- The ending image proves what changed in the world.

This file is standalone and uses only stdlib at runtime unless ASP mode is
requested, in which case storyworlds/asp.py is imported lazily.
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
# Core entities
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    e: object | None = None
    inst: object | None = None
    mys: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "fairy", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "elf"}:
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
class Setting:
    place: str
    indoors: bool = False
    mood: str = "gentle"
    affords: set[str] = field(default_factory=set)
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
class Instrument:
    id: str
    label: str
    phrase: str
    sound: str
    use: str
    twist: str
    clue: str
    effect: str
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
class Mystery:
    id: str
    label: str
    phrase: str
    source: str
    hidden_by: str
    reveal: str
    solved_by: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    world: object | None = None
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


# ---------------------------------------------------------------------------
# Content registries
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
    "lantern_glen": Setting(place="the lantern glen", indoors=False, mood="golden", affords={"sing"}),
    "rose_tower": Setting(place="the rose tower", indoors=True, mood="quiet", affords={"sing"}),
    "moon_pond": Setting(place="the moon pond", indoors=False, mood="silver", affords={"sing"}),
}

INSTRUMENTS = {
    "baton": Instrument(
        id="baton",
        label="baton",
        phrase="a pearl baton with a ribbon knot",
        sound="a soft tick-tick and a bright hum",
        use="conduct the singing",
        twist="turn the baton sideways",
        clue="the ribbon knot loosened",
        effect="the melody rose clear and true",
        tags={"sing", "baton", "twist"},
    ),
    "silver_baton": Instrument(
        id="silver_baton",
        label="silver baton",
        phrase="a silver baton that glimmered like moonlight",
        sound="a silver chime",
        use="guide the choir",
        twist="tip the baton toward the pond",
        clue="a moon-spark flashed at the tip",
        effect="the hidden note answered at once",
        tags={"sing", "baton", "twist"},
    ),
}

MYSTERIES = {
    "lost_note": Mystery(
        id="lost_note",
        label="lost note",
        phrase="a lost note in the song",
        source="a hush behind the lilies",
        hidden_by="a curtain of reeds",
        reveal="the reed curtain opened",
        solved_by="the melody itself",
        tags={"mystery", "solve"},
    ),
    "sleeping_chime": Mystery(
        id="sleeping_chime",
        label="sleeping chime",
        phrase="a sleeping chime under the stone bench",
        source="a sleepy stone bench",
        hidden_by="moss and dust",
        reveal="the moss slid away",
        solved_by="a clear, brave note",
        tags={"mystery", "solve"},
    ),
}

CHARACTER_TEMPLATES = [
    ("Luna", "fairy", "curious"),
    ("Mira", "fairy", "gentle"),
    ("Pip", "fairy", "brave"),
    ("Nell", "girl", "bright"),
]

FAMILY_TITLES = {"fairy": "young fairy", "girl": "girl"}
MOODS = ["curious", "hopeful", "nervous", "brave", "gentle"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    instrument: str
    mystery: str
    name: str
    kind: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
    p: object | None = None
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for i in INSTRUMENTS:
            for m in MYSTERIES:
                combos.append((s, i, m))
    return combos


def reasonableness_check(params: StoryParams) -> None:
    if params.instrument not in INSTRUMENTS:
        pass
    if params.mystery not in MYSTERIES:
        pass
    if params.setting not in SETTINGS:
        pass


def _init_entity(name: str, kind: str, trait: str) -> Entity:
    e = Entity(id=name, kind="character", type=kind, label=name)
    e.memes.update(curiosity=1.0, hope=1.0, worry=0.0, joy=0.0, relief=0.0, bravery=0.0)
    e.meters["spark"] = 1.0
    e.meters["voice"] = 1.0
    e.memes["trait"] = 1.0
    return e


def story_intro(world: World, hero: Entity, inst: Entity, mystery: Entity) -> None:
    world.say(
        f"Once in {world.setting.place}, {hero.id} was a {_safe_lookup(FAMILY_TITLES, hero.type)} who loved to sing."
    )
    world.say(
        f"{hero.id} carried {inst.phrase}, because it made {hero.pronoun('possessive')} songs feel like little stars."
    )
    world.say(
        f"But one evening, {mystery.phrase} was missing, and that made the music feel unfinished."
    )


def create_mystery(world: World, hero: Entity, mystery: Entity) -> None:
    hero.memes["curiosity"] += 1.0
    hero.memes["worry"] += 1.0
    mystery.hidden = True
    world.say(
        f"{hero.id} listened closely and heard only {mystery.source}."
    )
    world.say(
        f"That was the first clue, and it gave {hero.pronoun('object')} a gentle twist of worry."
    )


def search_and_twist(world: World, hero: Entity, inst: Entity, mystery: Entity) -> None:
    hero.memes["bravery"] += 1.0
    world.say(
        f"{hero.id} raised the {inst.label} and decided to {inst.twist}."
    )
    world.say(
        f"At once, {inst.clue}."
    )
    world.say(
        f"{hero.id} followed the clue with a careful step, singing a soft line to keep fear away."
    )
    mystery.hidden = False
    world.say(
        f"Then {mystery.reveal}, and the hidden place finally showed itself."
    )


def solve_mystery(world: World, hero: Entity, inst: Entity, mystery: Entity) -> None:
    hero.memes["joy"] += 1.5
    hero.memes["hope"] += 1.0
    hero.memes["worry"] = 0.0
    hero.memes["relief"] += 1.0
    inst.meters["shine"] = inst.meters.get("shine", 0.0) + 1.0
    world.say(
        f"{hero.id} sang louder, and {inst.effect}."
    )
    world.say(
        f"The {mystery.label} was solved because the song and the {inst.label} worked together."
    )


def ending_image(world: World, hero: Entity, inst: Entity, mystery: Entity) -> None:
    world.say(
        f"In the end, {hero.id} smiled beside {inst.phrase}, and the moonlight made {mystery.phrase} seem kind instead of strange."
    )


# ---------------------------------------------------------------------------
# World runner
# ---------------------------------------------------------------------------
def tell(setting: Setting, instrument: Instrument, mystery: Mystery,
         hero_name: str, hero_kind: str, trait: str) -> World:
    world = World(setting=setting)
    hero = world.add(_init_entity(hero_name, hero_kind, trait))
    inst = world.add(Entity(
        id=instrument.id,
        kind="thing",
        type="instrument",
        label=instrument.label,
        phrase=instrument.phrase,
    ))
    mys = world.add(Entity(
        id=mystery.id,
        kind="thing",
        type="mystery",
        label=mystery.label,
        phrase=mystery.phrase,
        hidden=True,
    ))

    world.facts.update(hero=hero, instrument=inst, mystery=mys, setting=setting)
    story_intro(world, hero, inst, mys)
    world.para()
    create_mystery(world, hero, mys)
    world.para()
    search_and_twist(world, hero, inst, mys)
    solve_mystery(world, hero, inst, mys)
    world.para()
    ending_image(world, hero, inst, mys)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    inst = _safe_fact(world, f, "instrument")
    mys = _safe_fact(world, f, "mystery")
    return [
        f'Write a fairy tale for a small child about {hero.id}, a {hero.type}, who loves to sing with a {inst.label}.',
        f'Write a short story with a mystery to solve, where a {inst.label} helps {hero.id} find the missing {mys.label}.',
        f'Write a gentle fairy tale that includes the words "sing" and "baton" and ends with a solved mystery.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    inst = _safe_fact(world, world.facts, "instrument")
    mys = _safe_fact(world, world.facts, "mystery")
    setting = _safe_fact(world, world.facts, "setting")
    return [
        QAItem(
            question=f"Who loved to sing in {setting.place}?",
            answer=f"{hero.id}, a {_safe_lookup(FAMILY_TITLES, hero.type)}, loved to sing in {setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.id} carry while looking for the mystery?",
            answer=f"{hero.id} carried {inst.phrase} while looking for {mys.phrase}.",
        ),
        QAItem(
            question=f"What made the mystery easier to solve?",
            answer=f"Turning the {inst.label} sideways and singing carefully helped solve the mystery.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} smiling beside {inst.phrase} after the mystery was solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a baton for in a song?",
            answer="A baton is a small stick or wand used to guide a song or group of singers.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something hidden or puzzling that you need clues to understand.",
        ),
        QAItem(
            question="Why do people sing?",
            answer="People sing to share feelings, tell a story, or make a moment feel bright and joyful.",
        ),
    ]


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting_ok(S) :- setting(S).
item_ok(I) :- instrument(I).
mystery_ok(M) :- mystery(M).

valid_story(S, I, M) :- setting_ok(S), item_ok(I), mystery_ok(M).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid in INSTRUMENTS:
        lines.append(asp.fact("instrument", iid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld: sing, baton, mystery to solve.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--kind", choices=["fairy", "girl"])
    ap.add_argument("--trait", choices=["curious", "hopeful", "nervous", "brave", "gentle"])
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
    combos = [
        c for c in combos
        if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
        and (getattr(args, "instrument", None) is None or c[1] == getattr(args, "instrument", None))
        and (getattr(args, "mystery", None) is None or c[2] == getattr(args, "mystery", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, instrument, mystery = rng.choice(list(combos))
    name, kind, trait = rng.choice(CHARACTER_TEMPLATES)
    if getattr(args, "name", None):
        name = getattr(args, "name", None)
    if getattr(args, "kind", None):
        kind = getattr(args, "kind", None)
    if getattr(args, "trait", None):
        trait = getattr(args, "trait", None)
    return StoryParams(setting=setting, instrument=instrument, mystery=mystery, name=name, kind=kind, trait=trait)


def generate(params: StoryParams) -> StorySample:
    reasonableness_check(params)
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(INSTRUMENTS, params.instrument),
        _safe_lookup(MYSTERIES, params.mystery),
        params.name,
        params.kind,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.hidden:
            bits.append("hidden=True")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        models = asp_valid_combos()
        print(f"{len(models)} compatible setting/instrument/mystery combos:")
        for item in models:
            print("  ", item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for setting in SETTINGS:
            for instrument in INSTRUMENTS:
                for mystery in MYSTERIES:
                    p = StoryParams(setting=setting, instrument=instrument, mystery=mystery,
                                     name="Luna", kind="fairy", trait="curious")
                    samples.append(generate(p))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
