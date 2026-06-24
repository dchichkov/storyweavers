#!/usr/bin/env python3
"""
A small storyworld for a folk-tale style conflict about bran and geology.

Seed tale:
---
In a village by a low stone hill, a kind miller girl named Mina loved to save bran
for the hens. One spring, the old hill began to crack after many hard rains.
The village shepherd said the hill was only dirt, but Mina's grandfather said it
was a true stone ridge with hidden layers. When the goats kept nibbling Mina's
bran sack near the slope, the sack ripped open and bran spilled everywhere.
Mina worried the crumbs would blow into the crack and make a mess.

She wanted to run away and hide, but her grandmother told her to look closely.
Mina used a little shovel, brushed away the bran, and saw tiny pebbles and
stripes in the dirt. The shepherd saw them too and admitted the hill had layers.
Together they moved the bran to the barn and marked the crack with a stick so
no goat would trip. Mina learned that careful eyes can calm a conflict.

World model:
- Physical meters: spilled bran, crack width, wet soil, gathered sacks, stored grain.
- Emotional memes: pride, worry, patience, apology, trust, conflict.
- The story turns when a real geological clue resolves a village argument.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    grain: object | None = None
    hazard: object | None = None
    hero: object | None = None
    kin: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they" if self.plural else "it",
                "object": "them" if self.plural else "it",
                "possessive": "their" if self.plural else "its"}[case]
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
    place: str = "the village"
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
class Hazard:
    id: str
    label: str
    clue: str
    turns: str
    risk: str
    kind: str = "geology"
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
class Remedy:
    id: str
    label: str
    tool: str
    action: str
    calming: str
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
    hazard: str
    remedy: str
    name: str
    gender: str
    kin: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


SETTINGS = {
    "village": Setting(place="the village", affords={"crack"}),
    "hill": Setting(place="the old hill", affords={"crack"}),
    "barnyard": Setting(place="the barnyard", affords={"spill"}),
}

HAZARDS = {
    "hillcrack": Hazard(
        id="hillcrack",
        label="stone hill",
        clue="tiny stripes in the dirt",
        turns="cracked",
        risk="might split open",
    ),
    "washout": Hazard(
        id="washout",
        label="mud bank",
        clue="loose pebbles and wet soil",
        turns="washed out",
        risk="might slide away",
    ),
}

REMEDIES = {
    "shovel": Remedy(
        id="shovel",
        label="a little shovel",
        tool="shovel",
        action="brush away the bran and mark the crack",
        calming="settled the argument",
    ),
    "plank": Remedy(
        id="plank",
        label="a flat plank",
        tool="plank",
        action="cover the weak place",
        calming="made the path safer",
    ),
}

GIRL_NAMES = ["Mina", "Tali", "Nora", "Lina", "Suri"]
BOY_NAMES = ["Bram", "Eli", "Pio", "Toma", "Rafi"]


class StoryWorld:
    pass


def aspire_reasonable(hazard: Hazard, remedy: Remedy) -> bool:
    if hazard.id == "hillcrack" and remedy.id == "shovel":
        return True
    if hazard.id == "washout" and remedy.id == "plank":
        return True
    return False


def explain_rejection(hazard: Hazard, remedy: Remedy) -> str:
    return (
        f"(No story: {remedy.label} does not fit the need for {hazard.label}. "
        f"The conflict must be resolved by a clue that truly belongs to the land.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale storyworld about bran and geology.")
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--kin", choices=["grandmother", "grandfather"])
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
    hazard = getattr(args, "hazard", None) or rng.choice(list(HAZARDS))
    remedy = getattr(args, "remedy", None) or rng.choice(list(REMEDIES))
    if not aspire_reasonable(_safe_lookup(HAZARDS, hazard), _safe_lookup(REMEDIES, remedy)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    kin = getattr(args, "kin", None) or rng.choice(["grandmother", "grandfather"])
    return StoryParams(hazard=hazard, remedy=remedy, name=name, gender=gender, kin=kin)


def _setup_world(params: StoryParams) -> tuple[World, Entity, Entity, Entity, Entity]:
    world = World(SETTINGS["village"])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    kin = world.add(Entity(id="Kin", kind="character", type=params.kin))
    grain = world.add(Entity(
        id="bran_sack",
        type="sack",
        label="bran sack",
        phrase="a full sack of bran",
        owner=hero.id,
        caretaker=kin.id,
        meters={"bran": 0.0, "spilled": 0.0},
    ))
    hazard = world.add(Entity(
        id="land",
        type="land",
        label=_safe_lookup(HAZARDS, params.hazard).label,
        phrase=_safe_lookup(HAZARDS, params.hazard).label,
        meters={"crack": 0.0, "soil": 0.0},
        memes={"conflict": 0.0},
    ))
    return world, hero, kin, grain, hazard


def tell(params: StoryParams) -> World:
    world, hero, kin, grain, hazard = _setup_world(params)
    h = _safe_lookup(HAZARDS, params.hazard)
    r = _safe_lookup(REMEDIES, params.remedy)

    hero.memes["love_bran"] = 1.0
    kin.memes["pride"] = 1.0

    world.say(f"{hero.id} was a little {params.gender} who helped keep the village grain bins full.")
    world.say(f"{hero.pronoun().capitalize()} loved bran, the dusty golden husk left from the mill.")
    world.say(f"Near the edge of {world.setting.place}, the old {h.label} had a bad habit of {h.turns} after hard rain.")

    world.para()
    world.say(
        f"One spring day, goats wandered close, and {hero.id} saw {hero.pronoun('possessive')} "
        f"{grain.label} wobble near the slope."
    )
    grain.meters["bran"] += 1
    grain.meters["spilled"] += 1
    hazard.meters["crack"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"Then the sack tore, and bran spilled over the ground. {h.clue.capitalize()} showed in the dirt, "
        f"and that made the village argue."
    )
    hazard.memes["conflict"] += 1
    kin.memes["conflict"] += 1
    kin.memes["warning"] += 1

    world.para()
    world.say(
        f"Some said the hill was only loose soil, but {hero.id}'s {params.kin} said it was a true stone ridge with hidden layers."
    )
    world.say(
        f"{hero.id} felt torn between the two voices and wanted to hide the mess, but {hero.pronoun('possessive')} {params.kin} knelt beside the crack."
    )
    world.say(
        f'"Look closely," {params.kin} said. "The land tells the truth to patient eyes."'
    )

    world.para()
    world.say(
        f"So {hero.id} picked up {r.label} and used {r.tool} to {r.action}."
    )
    hazard.memes["conflict"] = 0.0
    kin.memes["conflict"] = 0.0
    kin.memes["trust"] = 1.0
    hero.memes["pride"] += 1
    hero.memes["calm"] += 1
    grain.meters["spilled"] = 0.0
    grain.meters["stored"] = 1.0
    world.say(
        f"Under the crumbs, {hero.id} found tiny pebbles and neat stripes in the earth. "
        f"The shepherd and the neighbors saw the same clue and stopped arguing."
    )
    world.say(
        f"Together they moved the bran to the barn, set a stick by the crack, and kept the goats away. "
        f"In the quiet after that, the old hill was not a mystery anymore; it was a known stone place with layers."
    )

    world.facts.update(
        hero=hero,
        kin=kin,
        grain=grain,
        hazard=h,
        remedy=r,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    h: Hazard = _safe_fact(world, f, "hazard")
    r: Remedy = _safe_fact(world, f, "remedy")
    return [
        f'Write a folk-tale style story for a young child about {hero.id}, bran, and a {h.label} that seems to {h.turns}.',
        f"Tell a gentle conflict story where a child uses {r.label} to understand the land better.",
        f'Write a short story that includes bran, stone, and a family argument that ends in calm.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    kin: Entity = _safe_fact(world, f, "kin")
    h: Hazard = _safe_fact(world, f, "hazard")
    r: Remedy = _safe_fact(world, f, "remedy")
    return [
        QAItem(
            question=f"What did {hero.id} find near the old {h.label}?",
            answer=f"{hero.id} found a torn bran sack and tiny pebbles and stripes in the dirt near the old {h.label}.",
        ),
        QAItem(
            question=f"Why did the village start to argue about the land?",
            answer=f"The village argued because some people thought the hill was only loose soil, but {kin.id} said it was a stone ridge with hidden layers.",
        ),
        QAItem(
            question=f"How did {hero.id} help calm the conflict?",
            answer=f"{hero.id} used {r.label} to brush away the bran and show the real layers in the earth, which settled the disagreement.",
        ),
        QAItem(
            question=f"What happened to the bran by the end of the story?",
            answer="The bran was gathered up and moved to the barn so it would not spill around the crack anymore.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bran?",
            answer="Bran is the dry outer part of grain, and people often feed it to animals or use it in baking.",
        ),
        QAItem(
            question="What is geology?",
            answer="Geology is the study of rocks, soil, and the shape of the land.",
        ),
        QAItem(
            question="What is a crack in the ground?",
            answer="A crack is a narrow split or opening in something hard like stone or dry earth.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} " + " ".join(bits))
    return "\n".join(lines)


ASP_RULES = r"""
hazard(H) :- land(H).
remedy(R) :- tool(R,_).
compatible(hillcrack, shovel).
compatible(washout, plank).
resolved(H,R) :- compatible(H,R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for hid in HAZARDS:
        lines.append(asp.fact("land", hid))
    for rid, rem in REMEDIES.items():
        lines.append(asp.fact("tool", rid, rem.tool))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [("village", "hillcrack", "shovel"), ("village", "washout", "plank")]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set((h, r) for _, h, r in valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH")
    print("only in asp:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


CURATED = [
    StoryParams(hazard="hillcrack", remedy="shovel", name="Mina", gender="girl", kin="grandmother"),
    StoryParams(hazard="washout", remedy="plank", name="Bram", gender="boy", kin="grandfather"),
]


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


def build_samples(args: argparse.Namespace) -> list[StorySample]:
    samples = []
    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(generate(p))
        return samples
    base = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    seen = set()
    i = 0
    while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
        rng = random.Random(base + i)
        i += 1
        try:
            p = resolve_params(args, rng)
        except StoryError as e:
            print(e)
            return []
        p.seed = base + i
        s = generate(p)
        if s.story in seen:
            continue
        seen.add(s.story)
        samples.append(s)
    return samples


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/2."))
        return
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
        return

    samples = build_samples(args)
    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
