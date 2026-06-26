#!/usr/bin/env python3
"""
A small mythic storyworld about a child hero, an allergic mystery, a tense
investigation, and a gentle resolution.
"""

from __future__ import annotations

import argparse
import copy
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister", "aunt"}
        male = {"boy", "father", "man", "brother", "uncle"}
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
    indoors: bool = False
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
class Clue:
    id: str
    label: str
    phrase: str
    reveals: str
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
class Curse:
    id: str
    label: str
    symptom: str
    source: str
    worsens_with: str
    expand: str
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
class Remedy:
    id: str
    label: str
    phrase: str
    action: str
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    parent_type: str
    clue: str
    curse: str
    remedy: str
    seed: Optional[int] = None
    params: object | None = None
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
    "forest": Setting("the old forest", False, {"seek", "listen", "follow"}),
    "temple": Setting("the stone temple", True, {"seek", "listen", "follow"}),
    "harbor": Setting("the quiet harbor", False, {"seek", "listen", "follow"}),
}

CLUES = {
    "yellow_pollen": Clue(
        id="yellow_pollen",
        label="yellow pollen",
        phrase="a pinch of yellow pollen",
        reveals="the flowers were the hidden source",
        tags={"allergic", "mystery"},
    ),
    "honey_smell": Clue(
        id="honey_smell",
        label="honey smell",
        phrase="a sweet honey smell",
        reveals="the beehive was hiding in the roots",
        tags={"mystery"},
    ),
    "silver_dust": Clue(
        id="silver_dust",
        label="silver dust",
        phrase="silver dust on the wind",
        reveals="the moon-statue was shedding old powder",
        tags={"myth"},
    ),
}

CURSES = {
    "sneezing": Curse(
        id="sneezing",
        label="sneezing",
        symptom="sneeze",
        source="the pollen",
        worsens_with="wind",
        expand="spread wider",
        tags={"allergic", "suspense"},
    ),
    "watery_eyes": Curse(
        id="watery_eyes",
        label="watery eyes",
        symptom="tear up",
        source="the dust",
        worsens_with="darkness",
        expand="grow brighter",
        tags={"mystery", "suspense"},
    ),
}

REMEDIES = {
    "mask": Remedy(
        id="mask",
        label="a soft cloth mask",
        phrase="a soft cloth mask",
        action="cover her nose and mouth",
        helps={"sneezing"},
        tags={"allergic"},
    ),
    "wash": Remedy(
        id="wash",
        label="river water",
        phrase="river water in a clay bowl",
        action="wash the pollen away",
        helps={"sneezing", "watery_eyes"},
        tags={"myth"},
    ),
    "veil": Remedy(
        id="veil",
        label="a silver veil",
        phrase="a silver veil",
        action="shield her from the dust",
        helps={"watery_eyes"},
        tags={"myth"},
    ),
}

HERO_NAMES = ["Mira", "Nia", "Tala", "Iris", "Lea", "Sora", "Anya", "Lina"]
PARENT_NAMES = ["mother", "father", "aunt", "uncle"]
HERO_TYPES = ["girl", "boy"]
TRAITS = ["curious", "brave", "gentle", "sharp-eyed", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for clue in CLUES:
            for curse in CURSES:
                for remedy in REMEDIES:
                    if clue == "yellow_pollen" and curse != "sneezing":
                        continue
                    if clue == "silver_dust" and remedy not in {"wash", "veil"}:
                        continue
                    if curse == "sneezing" and remedy not in {"mask", "wash"}:
                        continue
                    combos.append((place, clue, curse, remedy))
    return [(a, b, c) for a, b, c, _ in combos]


def reasonableness_gate(clue: Clue, curse: Curse, remedy: Remedy) -> bool:
    if clue.id == "yellow_pollen" and curse.id != "sneezing":
        return False
    if curse.id == "sneezing" and remedy.id not in {"mask", "wash"}:
        return False
    if curse.id == "watery_eyes" and remedy.id not in {"wash", "veil"}:
        return False
    return True


def build_story(world: World, hero: Entity, parent: Entity, clue: Clue, curse: Curse, remedy: Remedy) -> None:
    hero.memes["curious"] = 1
    world.say(
        f"Long ago, {hero.id} walked beneath {world.setting.place} as if the path itself were listening."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved to look for signs, and today {hero.pronoun()} sought {clue.phrase}."
    )
    world.say(
        f"At the edge of the trail, {hero.pronoun('possessive')} {parent.label} warned softly that something unseen was making {hero.pronoun('object')} {curse.symptom}."
    )

    world.para()
    hero.memes["unease"] = 1
    world.say(
        f"The air grew tense. Each breath felt smaller, and the mystery seemed to {curse.expand} with every step."
    )
    world.say(
        f"{hero.id} noticed {clue.phrase}, and then the trail answered: {clue.reveals}."
    )
    hero.meters["exposure"] = 1
    hero.meters[curse.id] = 1
    if curse.id == "sneezing":
        hero.meters["sneeze"] = 1
    else:
        hero.meters["tear"] = 1

    world.para()
    world.say(
        f"{parent.id} knelt beside {hero.id} and held out {remedy.phrase}. "
        f"\"We can {remedy.action},\" {hero.pronoun('possessive')} {parent.label} said, \"and solve this the gentle way.\""
    )
    if remedy.id == "wash":
        world.say(
            f"They washed the dust away in a quiet bowl, and the rough feeling began to fade."
        )
    elif remedy.id == "mask":
        world.say(
            f"{hero.id} wore the cloth mask, and the wind could no longer carry the pollen straight in."
        )
    else:
        world.say(
            f"The silver veil caught the moon-sheen, and the strange dust could not trouble {hero.pronoun('object')} anymore."
        )

    hero.memes["relief"] = 1
    hero.memes["curious"] = 2
    hero.meters[curse.id] = 0
    hero.meters["exposure"] = 0
    world.facts.update(hero=hero, parent=parent, clue=clue, curse=curse, remedy=remedy)


def tell(setting: Setting, clue: Clue, curse: Curse, remedy: Remedy, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    build_story(world, hero, parent, clue, curse, remedy)
    return world


def predict_resolution(world: World, hero: Entity, curse: Curse, remedy: Remedy) -> bool:
    sim = world.copy()
    sim.get(hero.id).meters[curse.id] = 1
    sim.get(hero.id).meters["exposure"] = 1
    return remedy.id in {"wash", "mask", "veil"}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-like story for a young child that includes "{f["clue"].label}" and the word "allergic".',
        f"Tell a suspenseful story where {f['hero'].id} must solve why the path makes {f['hero'].pronoun('object')} {f['curse'].symptom}.",
        f"Write a gentle mystery about {f['hero'].id}, a hidden cause, and a remedy that helps the problem fade.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, clue, curse, remedy = f["hero"], f["parent"], f["clue"], f["curse"], f["remedy"]
    return [
        QAItem(
            question=f"Who was trying to solve the mystery in {world.setting.place}?",
            answer=f"It was {hero.id}, a {hero.type} who walked the path with {hero.pronoun('possessive')} {parent.label} and kept looking for clues.",
        ),
        QAItem(
            question=f"What clue helped explain the strange feeling?",
            answer=f"The clue was {clue.phrase}, and it showed that {clue.reveals}.",
        ),
        QAItem(
            question=f"Why did {hero.id} start to feel worse?",
            answer=f"{hero.id} started to {curse.symptom} because the hidden {curse.source} was in the air, and the mystery grew more suspenseful before it was solved.",
        ),
        QAItem(
            question=f"What helped {hero.id} in the end?",
            answer=f"{remedy.phrase} helped because it could {remedy.action}, and that made the problem settle down.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = [
        QAItem(
            question="What does it mean to be allergic?",
            answer="Being allergic means your body reacts strongly to something harmless to other people, like pollen or dust.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a problem where the cause is not obvious at first, so you have to look for clues.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the nervous feeling you get when you wonder what will happen next.",
        ),
    ]
    if f["clue"].id == "yellow_pollen":
        out.append(QAItem(
            question="What is pollen?",
            answer="Pollen is a tiny powder from flowers and plants that the wind can carry through the air.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== prompts ==")
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


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
clue(yellow_pollen).
clue(honey_smell).
clue(silver_dust).

curse(sneezing).
curse(watery_eyes).

remedy(mask).
remedy(wash).
remedy(veil).

reasonably_matches(yellow_pollen, sneezing).
reasonably_matches(silver_dust, watery_eyes).

helps(mask, sneezing).
helps(wash, sneezing).
helps(wash, watery_eyes).
helps(veil, watery_eyes).

valid(C, U, R) :- clue(C), curse(U), remedy(R), reasonably_matches(C, U), helps(R, U).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for uid in CURSES:
        lines.append(asp.fact("curse", uid))
    for rid in REMEDIES:
        lines.append(asp.fact("remedy", rid))
    lines.append(asp.fact("reasonably_matches", "yellow_pollen", "sneezing"))
    lines.append(asp.fact("reasonably_matches", "silver_dust", "watery_eyes"))
    for rid, rem in REMEDIES.items():
        for u in rem.helps:
            lines.append(asp.fact("helps", rid, u))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set()
    for clue in CLUES.values():
        for curse in CURSES.values():
            for remedy in REMEDIES.values():
                if reasonableness_gate(clue, curse, remedy):
                    py.add((clue.id, curse.id, remedy.id))
    asp_set = set(asp_valid())
    if py == asp_set:
        print(f"OK: clingo gate matches python gate ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - asp_set))
    print("asp-only:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic mystery storyworld with an allergic suspenseful turn.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--curse", choices=CURSES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--trait", choices=TRAITS)
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
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    curse = getattr(args, "curse", None) or rng.choice(list(CURSES))
    remedy = getattr(args, "remedy", None) or rng.choice(list(REMEDIES))
    if not reasonableness_gate(_safe_lookup(CLUES, clue), _safe_lookup(CURSES, curse), _safe_lookup(REMEDIES, remedy)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(HERO_TYPES)
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENT_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    return StoryParams(place=place, hero_name=name, hero_type=gender, parent_type=parent, clue=clue, curse=curse, remedy=remedy)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(CLUES, params.clue),
        _safe_lookup(CURSES, params.curse),
        _safe_lookup(REMEDIES, params.remedy),
        params.hero_name,
        params.hero_type,
        params.parent_type,
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
        vals = asp_valid()
        print(f"{len(vals)} valid combinations:")
        for t in vals:
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for clue in CLUES:
            for curse in CURSES:
                for remedy in REMEDIES:
                    if reasonableness_gate(_safe_lookup(CLUES, clue), _safe_lookup(CURSES, curse), _safe_lookup(REMEDIES, remedy)):
                        params = StoryParams(
                            place=getattr(args, "place", None) or "forest",
                            hero_name=getattr(args, "name", None) or "Mira",
                            hero_type=getattr(args, "gender", None) or "girl",
                            parent_type=getattr(args, "parent", None) or "mother",
                            clue=clue,
                            curse=curse,
                            remedy=remedy,
                            seed=base_seed,
                        )
                        samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(100, getattr(args, "n", None) * 50):
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
            header = f"### {p.hero_name}: {p.clue} / {p.curse} / {p.remedy}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
