#!/usr/bin/env python3
"""
storyworlds/worlds/grand_bad_ending_flashback_bravery_animal_story.py
=====================================================================

A small animal story world with a brave child, a remembered flashback, and a
gentle bad ending.

Premise:
- A young animal wants something at a risky place.
- A grand elder remembers a past moment and warns them.
- The child is brave and tries anyway.
- The attempt fails, but the child learns something and ends the day changed.

The stories are intentionally compact, concrete, and child-facing.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder_ent: object | None = None
    hero: object | None = None
    prize_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "son", "father", "dad", "buck"}
        female = {"girl", "daughter", "mother", "mom", "doe"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
    place: str = "the grand old bridge"
    afford: set[str] = field(default_factory=set)
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
class Hazard:
    id: str
    label: str
    verb: str
    rush: str
    risk: str
    zone: set[str]
    weather: str
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
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
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
class StoryParams:
    place: str
    hazard: str
    prize: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
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
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "bridge": Setting(place="the grand old bridge", afford={"river", "wind"}),
    "bank": Setting(place="the river bank", afford={"river"}),
    "tree": Setting(place="the grand hollow tree", afford={"wind"}),
}

HAZARDS = {
    "river": Hazard(
        id="river",
        label="river",
        verb="cross the river",
        rush="run onto the bridge",
        risk="slip into the water",
        zone={"feet", "legs"},
        weather="rainy",
        tags={"water", "river"},
    ),
    "wind": Hazard(
        id="wind",
        label="wind",
        verb="fly the kite",
        rush="dash into the open field",
        risk="lose the kite to the sky",
        zone={"torso", "arms"},
        weather="windy",
        tags={"wind", "sky"},
    ),
}

PRIZES = {
    "kite": Prize(
        id="kite",
        label="kite",
        phrase="a bright red kite",
        region="arms",
        tags={"wind", "sky"},
    ),
    "basket": Prize(
        id="basket",
        label="basket",
        phrase="a berry basket full of sweet berries",
        region="hands",
        tags={"river", "food"},
    ),
    "boat": Prize(
        id="boat",
        label="toy boat",
        phrase="a small toy boat",
        region="hands",
        tags={"water", "river"},
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Pip", "Nia", "Rose", "Tia"]
BOY_NAMES = ["Toby", "Finn", "Rory", "Ben", "Milo", "Ollie"]
TRAITS = ["brave", "curious", "gentle", "restless", "kind"]

# ---------------------------------------------------------------------------
# Story validation
# ---------------------------------------------------------------------------
def prize_at_risk(hazard: Hazard, prize: Prize) -> bool:
    return prize.region in hazard.zone


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for hazard_id in setting.afford:
            haz = _safe_lookup(HAZARDS, hazard_id)
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(haz, prize):
                    combos.append((place, hazard_id, prize_id))
    return combos


def explain_rejection(hazard: Hazard, prize: Prize) -> str:
    return (
        f"(No story: {hazard.verb} does not threaten {prize.label} in a believable "
        f"way here. Pick a prize worn on the same body area the hazard reaches.)"
    )


# ---------------------------------------------------------------------------
# Pronoun/name helpers
# ---------------------------------------------------------------------------
def elder_label(elder: str) -> str:
    return {"grandmother": "Grandmother", "grandfather": "Grandfather"}.get(elder, elder)


def elder_possessive(elder: str) -> str:
    return {"grandmother": "Grandmother's", "grandfather": "Grandfather's"}.get(elder, elder.capitalize() + "'s")


def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------
def tell(setting: Setting, hazard: Hazard, prize: Prize, hero_name: str, gender: str,
         elder: str, trait: str) -> World:
    world = World(setting)
    world.weather = hazard.weather

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type="girl" if gender == "girl" else "boy",
        traits=["little", trait, "animal"],
        memes={"bravery": 0.0, "sadness": 0.0, "memory": 0.0},
    ))
    elder_ent = world.add(Entity(
        id="Elder",
        kind="character",
        type="grandmother" if elder == "grandmother" else "grandfather",
        label=elder_label(elder),
        traits=["grand", "careful", "animal"],
        memes={"worry": 0.0},
    ))
    prize_ent = world.add(Entity(
        id="Prize",
        type=prize.id,
        label=prize.label,
        phrase=prize.phrase,
        owner=hero.id,
        caretaker=elder_ent.id,
    ))

    # Act 1: setup
    world.say(
        f"{hero.id} was a little {trait} animal who loved {prize.phrase}."
    )
    world.say(
        f"Near {setting.place}, {hero.id} found {prize.phrase} waiting by the risky edge."
    )
    world.say(
        f"{hero.id}'s {elder_ent.label} called it the grand path and kept a close eye on it."
    )

    # Flashback
    world.para()
    elder_ent.memes["memory"] += 1
    world.say(
        f"That made {elder_ent.label} remember a flashback from long ago."
    )
    world.say(
        f"Once, when the sky turned harsh, {elder_ent.label} had seen a small animal "
        f"lose its footing there and cry for help."
    )
    world.say(
        f"{elder_ent.label} pointed at the old spot and said, "
        f"\"I still remember how fast that place can turn mean.\""
    )

    # Act 2: warning and bravery
    world.para()
    world.say(
        f"{hero.id} wanted to {hazard.verb}, even after hearing the warning."
    )
    hero.memes["bravery"] += 1
    world.say(
        f"{hero.id} puffed up with bravery and said, \"I can do it!\""
    )
    world.say(
        f"So {hero.id} {hazard.rush} with {prize.label} held tight."
    )
    world.zone = set(hazard.zone)

    # Failure state
    if prize.region in hazard.zone:
        prize_ent.meters["safe"] = 0.0
        hero.memes["sadness"] += 1
        world.say(
            f"But the {hazard.label} was stronger than the brave idea."
        )
        if hazard.id == "river":
            world.say(
                f"A slick step sent {prize.label} spinning, and the water carried it away."
            )
            world.say(
                f"{hero.id} got to the bank wet and empty-handed, while {elder_ent.label} hurried after."
            )
        else:
            world.say(
                f"A hard gust whisked {prize.label} high, and it vanished into the clouds."
            )
            world.say(
                f"{hero.id} stood still in the wind, watching the sky keep what it had taken."
            )
    else:
        pass

    # Bad ending, but complete
    world.para()
    world.say(
        f"At the end, {hero.id} was brave, but the day ended badly."
    )
    world.say(
        f"{elder_ent.label} wrapped {hero.id} in a careful hug and promised a safer plan for tomorrow."
    )
    world.say(
        f"{hero.id} looked back at {setting.place} and remembered the flashback too."
    )

    world.facts.update(
        hero=hero,
        elder=elder_ent,
        prize=prize_ent,
        setting=setting,
        hazard=hazard,
        trait=trait,
        gender=gender,
        bad_end=True,
        flashback=True,
        brave=True,
        outcome="sad",
    )
    return world


# ---------------------------------------------------------------------------
# QA generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    elder = _safe_fact(world, f, "elder")
    hazard = _safe_fact(world, f, "hazard")
    prize = _safe_fact(world, f, "prize")
    return [
        f"Write a short animal story about {hero.id}, bravery, and a sad ending.",
        f"Tell a gentle flashback story where {elder.label} remembers a past danger and warns {hero.id}.",
        f"Write a child-friendly story in which {hero.id} tries to {hazard.verb} but the plan goes wrong.",
        f"Make the story include the word grand and end with a quiet, unhappy result for {prize.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    elder = _safe_fact(world, f, "elder")
    hazard = _safe_fact(world, f, "hazard")
    prize = _safe_fact(world, f, "prize")
    place = _safe_fact(world, f, "setting").place
    return [
        QAItem(
            question=f"Who was the brave little animal in the story?",
            answer=f"The brave little animal was {hero.id}, a small {f['trait']} animal.",
        ),
        QAItem(
            question=f"What did {elder.label} remember in the flashback?",
            answer=(
                f"{elder.label} remembered a time long ago when the same place was dangerous "
                f"and a small animal almost got hurt."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} want to do near {place}?",
            answer=f"{hero.id} wanted to {hazard.verb}.",
        ),
        QAItem(
            question=f"What happened to the {prize.label} at the end?",
            answer=(
                f"The {prize.label} was lost when the risky plan failed, so the ending was sad."
            ),
        ),
        QAItem(
            question=f"Why did the story end badly?",
            answer=(
                f"It ended badly because {hero.id} tried to be brave, but the hazard was too strong "
                f"and the prize was carried away."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does brave mean?",
            answer="Brave means being willing to do something scary or hard.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly remembers something that happened before.",
        ),
        QAItem(
            question="What is a grand place or grand thing?",
            answer="Grand means big, impressive, or important-looking.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(H, P) :- hazard(H), prize(P), hazard_zone(H, R), prize_region(P, R).
valid_place(Place, H, P) :- place(Place), affords(Place, H), prize_at_risk(H, P).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for h in sorted(setting.afford):
            lines.append(asp.fact("affords", pid, h))
    for hid, haz in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        for r in sorted(haz.zone):
            lines.append(asp.fact("hazard_zone", hid, r))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, prize.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_place/3."))
    return sorted(set(asp.atoms(model, "valid_place")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP matches Python reasonableness gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    print("  only in ASP:", sorted(clingo_set - python_set))
    print("  only in Python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world with a grand flashback, bravery, and a bad ending."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
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
    if getattr(args, "hazard", None) and getattr(args, "prize", None):
        haz = _safe_lookup(HAZARDS, getattr(args, "hazard", None))
        prize = _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not prize_at_risk(haz, prize):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "hazard", None) is None or c[1] == getattr(args, "hazard", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, hazard_id, prize_id = rng.choice(list(combos))
    prize = _safe_lookup(PRIZES, prize_id)
    gender = getattr(args, "gender", None) or "girl"
    name = getattr(args, "name", None) or choose_name(gender, rng)
    elder = getattr(args, "elder", None) or rng.choice(["grandmother", "grandfather"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, hazard=hazard_id, prize=prize_id, name=name,
                       gender=gender, elder=elder, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(HAZARDS, params.hazard),
        _safe_lookup(PRIZES, params.prize),
        params.name,
        params.gender,
        params.elder,
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- trace ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="bridge", hazard="river", prize="basket", name="Mina", gender="girl", elder="grandmother", trait="brave"),
    StoryParams(place="tree", hazard="wind", prize="kite", name="Toby", gender="boy", elder="grandfather", trait="curious"),
    StoryParams(place="bank", hazard="river", prize="boat", name="Pip", gender="girl", elder="grandmother", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_place/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible place/hazard/prize combos:")
        for c in combos:
            print("  ", c)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
