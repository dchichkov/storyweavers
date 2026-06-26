#!/usr/bin/env python3
"""
Standalone storyworld: folk tale with magic, a pile, typhus, and a bad ending.

This world tells a small classical tale in a folk style. A curious child or
young villager trusts a magic pile, ignores an elder's warning, and the story
ends badly when typhus comes to the house.
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
# World model
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    elder: object | None = None
    hero: object | None = None
    magic: object | None = None
    pile: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "maid", "queen", "elderwoman"}
        male = {"boy", "man", "father", "elderman", "son"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Setting:
    place: str
    indoors: bool = True
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
class Magic:
    id: str
    label: str
    phrase: str
    effect: str
    risk: str
    boon: str
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
class Pile:
    id: str
    label: str
    phrase: str
    kind: str
    region: str
    thing: bool = True
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def chars(self) -> list[Entity]:
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
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "cottage": Setting(place="the little cottage", indoors=True, affords={"magic", "pile"}),
    "village": Setting(place="the village lane", indoors=False, affords={"magic", "pile"}),
    "miller": Setting(place="the mill house", indoors=True, affords={"magic", "pile"}),
}

MAGICS = {
    "charm": Magic(
        id="charm",
        label="a bright charm",
        phrase="a bright charm with a gold thread",
        effect="glowed and sang softly",
        risk="hid the rot inside the pile",
        boon="made the pile seem warm and friendly",
    ),
    "spellbook": Magic(
        id="spellbook",
        label="a small spellbook",
        phrase="a small spellbook with blue beads",
        effect="whispered old words",
        risk="made the pile seem harmless",
        boon="promised easy luck",
    ),
}

PILES = {
    "rags": Pile(
        id="rags",
        label="the rag pile",
        phrase="a shabby pile of rags",
        kind="rags",
        region="floor",
    ),
    "straw": Pile(
        id="straw",
        label="the straw pile",
        phrase="a loose pile of straw",
        kind="straw",
        region="floor",
    ),
    "clothes": Pile(
        id="clothes",
        label="the clothes pile",
        phrase="a heap of old clothes",
        kind="clothes",
        region="floor",
    ),
}

NAMES = ["Mara", "Ivo", "Tess", "Anya", "Bram", "Nell", "Galen", "Siva"]
KINDS = ["girl", "boy"]
ELDERS = ["mother", "father", "grandmother", "grandfather"]
TRAITS = ["curious", "bold", "hasty", "dreamy", "stubborn"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def pile_at_risk(magic: Magic, pile: Pile) -> bool:
    return pile.kind in {"rags", "straw", "clothes"} and magic.id in {"charm", "spellbook"}


def select_reasonable_magic(pile: Pile) -> Optional[Magic]:
    for magic in MAGICS.values():
        if pile_at_risk(magic, pile):
            return magic
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for m in MAGICS:
            for p in PILES:
                out.append((place, m, p))
    return out


# ---------------------------------------------------------------------------
# Narrative
# ---------------------------------------------------------------------------
def _spreads_typhus(world: World) -> list[str]:
    out: list[str] = []
    for e in world.chars():
        if e.meters.get("exposure", 0.0) < 1.0:
            continue
        if e.meters.get("typhus", 0.0) >= 1.0:
            continue
        sig = ("typhus", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["typhus"] = 1.0
        e.memes["fear"] = e.memes.get("fear", 0.0) + 1.0
        out.append(f"{e.id} fell sick with typhus.")
    return out


def _magic_stirs(world: World, magic: Entity, pile: Entity) -> list[str]:
    out: list[str] = []
    sig = ("magic", magic.id, pile.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pile.meters["glow"] = pile.meters.get("glow", 0.0) + 1.0
    pile.meters["danger"] = pile.meters.get("danger", 0.0) + 1.0
    out.append(f"The {magic.label} made the {pile.label} glow.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    lines.extend(_spreads_typhus(world))
    if narrate:
        for line in lines:
            world.say(line)
    return lines


def folk_opening(world: World, hero: Entity, elder: Entity, pile: Entity, magic: Entity) -> None:
    world.say(
        f"Long ago, in {world.setting.place}, there lived {hero.id}, a {hero.type} who was "
        f"{next((t for t in hero.traits if t != 'little'), 'curious')} by nature."
    )
    world.say(
        f"One day {hero.id} found {pile.phrase} beside {magic.phrase}, and {magic.label} "
        f"{magic.effect} whenever {hero.id} touched {pile.label}."
    )
    world.say(
        f"{hero.id} loved the strange little wonder, but {elder.id} warned, "
        f'"Do not trust a pile that sits too still, for old dirt can hide old sickness."'
    )


def tempt(world: World, hero: Entity, magic: Entity, pile: Entity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1.0
    world.say(
        f"Still, {hero.id} wanted to keep the magic near, because {magic.boon}."
    )
    world.say(
        f"{hero.id} moved the {pile.label} closer to the bed and let the {magic.label} shine over it."
    )
    hero.meters["exposure"] = hero.meters.get("exposure", 0.0) + 1.0
    propagate(world, narrate=True)


def warning(world: World, elder: Entity, hero: Entity, pile: Entity) -> None:
    world.say(
        f'"That pile is not clean," said {elder.id}. "If you lie beside it, you may breathe its bad dust."'
    )


def ending_bad(world: World, hero: Entity, elder: Entity, pile: Entity, magic: Entity) -> None:
    world.say(
        f"But {hero.id} did not listen. By nightfall, the {magic.label} still glowed, the "
        f"{pile.label} still looked bright, and {hero.id} lay feverish under a thin blanket."
    )
    world.say(
        f"In the morning, {elder.id} burned the {pile.label} in the yard, but the smoke rose too late; "
        f"{hero.id} had already caught typhus, and the house became quiet as a grave."
    )


def tell(setting: Setting, hero_name: str, hero_type: str, elder_type: str,
         trait: str, magic_key: str, pile_key: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type, traits=["little", trait, "stubborn"]
    ))
    elder = world.add(Entity(
        id="Elder", kind="character", type=elder_type, label=f"the {elder_type}"
    ))
    magic_def = _safe_lookup(MAGICS, magic_key)
    pile_def = _safe_lookup(PILES, pile_key)
    magic = world.add(Entity(
        id=magic_def.id, type="thing", label=magic_def.label, phrase=magic_def.phrase
    ))
    pile = world.add(Entity(
        id=pile_def.id, type="thing", label=pile_def.label, phrase=pile_def.phrase, plural=True
    ))

    world.facts.update(hero=hero, elder=elder, magic=magic, pile=pile, setting=setting)

    folk_opening(world, hero, elder, pile, magic)
    world.para()
    warning(world, elder, hero, pile)
    tempt(world, hero, magic, pile)
    world.para()
    ending_bad(world, hero, elder, pile, magic)
    world.facts["bad_ending"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    elder: Entity = _safe_fact(world, f, "elder")
    magic: Entity = _safe_fact(world, f, "magic")
    pile: Entity = _safe_fact(world, f, "pile")
    return [
        f'Write a folk tale for a child about {hero.id}, {magic.label}, and {pile.label}, ending badly.',
        f"Tell a simple old-fashioned story where {hero.id} ignores {elder.id}'s warning about {pile.phrase}.",
        f'Write a short magic-and-warning story that uses the word "typhus" and has a bad ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    elder: Entity = _safe_fact(world, f, "elder")
    magic: Entity = _safe_fact(world, f, "magic")
    pile: Entity = _safe_fact(world, f, "pile")
    return [
        QAItem(
            question=f"Who was the story about in {world.setting.place}?",
            answer=f"It was about {hero.id}, a {hero.type} in {world.setting.place}, and the old warning from {elder.id}.",
        ),
        QAItem(
            question=f"What did {hero.id} find beside the pile?",
            answer=f"{hero.id} found {magic.phrase} beside {pile.phrase}. The magic made the pile seem bright and safe.",
        ),
        QAItem(
            question=f"Why did the tale end badly?",
            answer=(
                f"It ended badly because {hero.id} trusted the magic and stayed too near the dirty pile. "
                f"The bad dust and hidden sickness brought typhus to {hero.id}."
            ),
        ),
        QAItem(
            question=f"What did {elder.id} warn about?",
            answer=(
                f"{elder.id} warned that a still, dirty pile could hide sickness, and that lying beside it could make a child ill."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is typhus?",
            answer="Typhus is a dangerous sickness that can make a person very ill and feverish.",
        ),
        QAItem(
            question="What is a pile?",
            answer="A pile is a heap of things stacked together, like rags, straw, or old clothes.",
        ),
        QAItem(
            question="What does magic usually do in folk tales?",
            answer="Magic in folk tales can make odd things happen, but it is not always safe or wise to trust.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
pile_at_risk(M, P) :- magic(M), pile(P).
valid_story(Place, M, P) :- setting(Place), magic(M), pile(P), pile_at_risk(M, P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for mid in MAGICS:
        lines.append(asp.fact("magic", mid))
    for pid in PILES:
        lines.append(asp.fact("pile", pid))
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
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH")
    if py - cl:
        print("only in Python:", sorted(py - cl))
    if cl - py:
        print("only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story interface
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    magic: str
    pile: str
    name: str
    gender: str
    elder: str
    trait: str
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


CURATED = [
    StoryParams(place="cottage", magic="charm", pile="rags", name="Mara", gender="girl", elder="grandmother", trait="curious"),
    StoryParams(place="village", magic="spellbook", pile="straw", name="Ivo", gender="boy", elder="father", trait="bold"),
    StoryParams(place="miller", magic="charm", pile="clothes", name="Tess", gender="girl", elder="mother", trait="dreamy"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale world with magic, typhus, a pile, and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--pile", choices=PILES)
    ap.add_argument("--gender", choices=KINDS)
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--name")
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
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "magic", None) is None or c[1] == getattr(args, "magic", None))
        and (getattr(args, "pile", None) is None or c[2] == getattr(args, "pile", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, magic, pile = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(KINDS)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    elder = getattr(args, "elder", None) or rng.choice(ELDERS)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, magic=magic, pile=pile, name=name, gender=gender, elder=elder, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), params.name, params.gender, params.elder, params.trait, params.magic, params.pile)
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
        print("--- world trace ---")
        for e in sample.world.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            if e.kind == "thing" and e.label:
                bits.append(f"label={e.label}")
            print(f"{e.id}: {e.type} {' '.join(bits)}")
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
        print(f"{len(asp_valid_combos())} compatible stories")
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
            header = f"### {p.name}: {p.magic} + {p.pile} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
