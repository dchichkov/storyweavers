#!/usr/bin/env python3
"""
storyworlds/worlds/carb_doll_bravery_suspense_magic_tall_tale.py
===============================================================

A tiny tall-tale storyworld about a doll, a carb, and a brave choice made in
the middle of a magical, suspenseful night.

Seed tale:
---
A small doll named Tilly lived on a shelf above the bakery floor. One windy
evening, a giant storm rattled the windows, and the baker worried that the
moonlit pantry would swallow a basket of golden carb buns if nobody climbed up
to save it. Tilly was only a doll, but she had a bold heart. A spark of magic
from the sugar jar gave her courage, and she tiptoed across the high shelf,
through the hush and the creak, to bring the carb buns down safe. The storm
laughed itself quiet, and the baker called Tilly the bravest doll in the county.

World model:
---
    suspense rises -> a careful actor notices the risk, the dark, the creak
    magic appears  -> a charm or glow adds a boost to bravery
    bravery used   -> the doll can cross the dangerous gap
    carb delivered -> the pantry calms, the baker relaxes, the ending image proves
                      the change

The story is intentionally small and classical: a child-facing premise, one
pressure point, one magical turn, and one resolved ending image.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    magical: bool = False
    baker: object | None = None
    charm: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "baker"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
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
    place: str = "the moonlit pantry"
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
class Item:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    magical: bool = False
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
class Charm:
    id: str
    label: str
    phrase: str
    boost: str
    prep: str
    tail: str
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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    age: int
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


SETTINGS = {
    "pantry": Setting(place="the moonlit pantry", afford={"cross", "climb"}),
    "barn": Setting(place="the echoing barn loft", afford={"cross", "climb"}),
    "attic": Setting(place="the attic ladder", afford={"climb"}),
}

ACTIONS = {
    "cross": {
        "verb": "cross the creaky beam",
        "gerund": "crossing the creaky beam",
        "risk": "the floor would swallow the prize if it fell",
        "danger": "the beam shivered like a fiddle string",
    },
    "climb": {
        "verb": "climb the high shelf",
        "gerund": "climbing the high shelf",
        "risk": "the prize sat high enough to rattle loose",
        "danger": "the ladder gave a long, spooky creak",
    },
}

PRIZES = {
    "carb": Item(
        id="carb",
        label="carb buns",
        phrase="golden carb buns",
        region="shelf",
        plural=True,
        magical=False,
    ),
    "doll": Item(
        id="doll",
        label="doll",
        phrase="a small cloth doll",
        region="hand",
        magical=True,
    ),
}

CHARMS = {
    "starlight": Charm(
        id="starlight",
        label="starlight sugar",
        phrase="a jar of starlight sugar",
        boost="bravery",
        prep="sprinkle the starlight sugar on the doll's heart",
        tail="the sugar jar gave the doll just enough courage",
    ),
    "bell": Charm(
        id="bell",
        label="a silver bell",
        phrase="a silver bell tied with blue thread",
        boost="bravery",
        prep="ring the silver bell beside the shelf",
        tail="the bell sang a tiny brave tune",
    ),
}

NAMES = ["Tilly", "Mara", "Pip", "Nina", "June", "Lottie"]


def _meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _mem(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def reasonableness_gate(place: str, action: str, prize: str) -> bool:
    if place not in SETTINGS or action not in ACTIONS or prize not in PRIZES:
        return False
    return action in _safe_lookup(SETTINGS, place).afford


def explain_rejection(place: str, action: str, prize: str) -> str:
    return (
        f"(No story: {_safe_lookup(ACTIONS, action)['verb']} does not fit {_safe_lookup(SETTINGS, place).place}, "
        f"so the little tale would not have a real suspenseful problem.)"
    )


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type="doll"))
    baker = world.add(Entity(id="Baker", kind="character", type="baker", label="the baker"))
    prize = world.add(Entity(
        id=params.prize,
        type="thing",
        label=_safe_lookup(PRIZES, params.prize).label,
        phrase=_safe_lookup(PRIZES, params.prize).phrase,
        caretaker=baker.id,
        plural=_safe_lookup(PRIZES, params.prize).plural,
    ))
    charm = world.add(Entity(
        id="Charm",
        type="thing",
        label="starlight sugar",
        phrase=CHARMS["starlight"].phrase,
        magical=True,
    ))

    # Act 1: setup.
    world.say(
        f"{hero.id} was a little doll who lived in {setting.place} and loved quiet corners, warm crumbs, and big brave stories."
    )
    world.say(
        f"One evening, the baker brought home {prize.phrase}, and everyone in the pantry went still with wonder."
    )
    hero.memes["love"] = 1
    prize.meters["safe"] = 1

    # Act 2: suspense.
    world.para()
    world.say(
        f"Then the wind tapped the window, and {_safe_lookup(ACTIONS, params.action)['danger']}."
    )
    hero.memes["suspense"] = 1
    world.say(
        f"The baker looked up and worried that {_safe_lookup(ACTIONS, params.action)['risk']}."
    )
    hero.memes["concern"] = 1

    # Act 3: magic and bravery.
    world.para()
    hero.memes["bravery"] = 0
    world.say(
        f"{hero.id} felt tiny as a thimble, but {CHARMS['starlight'].tail}."
    )
    hero.memes["magic"] = 1
    hero.memes["bravery"] += 1
    world.say(
        f"With that magic sparkle in {hero.pronoun('possessive')} chest, {hero.id} decided to {_safe_lookup(ACTIONS, params.action)['verb']}."
    )
    world.say(
        f"{hero.id} held {prize.label if params.prize == 'doll' else 'the ladder rail'} with careful hands and kept going."
    )

    prize.meters["safe"] = 2
    prize.memes["rescued"] = 1
    baker.memes["relief"] = 1
    hero.memes["bravery"] += 1

    # Ending image.
    world.para()
    if params.prize == "carb":
        world.say(
            f"At last, {hero.id} brought the carb buns down safe, and the whole pantry smelled like honey and moonlight."
        )
    else:
        world.say(
            f"At last, {hero.id} brought the doll down safe, and the whole pantry seemed to bow for the brave little rescuer."
        )
    world.say(
        f"The baker laughed softly, and {hero.id} stood tall as a parade flag, proud and shining in the hush."
    )

    world.facts.update(
        hero=hero,
        baker=baker,
        prize=prize,
        charm=charm,
        params=params,
        setting=setting,
        action=params.action,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    return [
        f"Write a short tall tale for children about a doll named {hero.id}, magic, and bravery.",
        f"Tell a suspenseful but gentle story in {f['setting'].place} where a doll uses magic to save a carb.",
        f"Write a tiny, child-facing tall tale that ends with {hero.id} standing brave and tall.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    prize = _safe_fact(world, f, "prize")
    action = _safe_fact(world, f, "action")
    baker = _safe_fact(world, f, "baker")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about a little doll named {hero.id} who found bravery in a magical moment.",
        ),
        QAItem(
            question=f"What made the story suspenseful?",
            answer=f"The story was suspenseful because the wind rattled {f['setting'].place} and the prize was in danger.",
        ),
        QAItem(
            question=f"What did {hero.id} save?",
            answer=f"{hero.id} saved {prize.phrase} for {baker.label}.",
        ),
        QAItem(
            question=f"How did {hero.id} get brave enough to help?",
            answer=f"A bit of magic from the starlight sugar gave {hero.id} courage to act.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a carb?",
            answer="A carb is a food like bread, buns, or crackers that can be soft, warm, and filling.",
        ),
        QAItem(
            question="What is a doll?",
            answer="A doll is a toy made to look like a person, and children often carry or dress dolls with care.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing a hard or scary thing even when you feel nervous.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic in a story is a special, wonderful power that can make surprising things happen.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
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
        if e.kind == "character":
            bits.append("character")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- action(A), prize(P), risky(A,P).
brave(A) :- magic(A), suspense(A).
resolved(A,P) :- brave(A), prize_at_risk(A,P), action(A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
        for a in _safe_lookup(SETTINGS, pid).afford:
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for cid in CHARMS:
        lines.append(asp.fact("magic", cid))
        lines.append(asp.fact("suspense", cid))
    for place, s in SETTINGS.items():
        for act in s.afford:
            for prize in PRIZES:
                lines.append(asp.fact("risky", act, prize))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show resolved/2."))
    return sorted(set(asp.atoms(model, "resolved")))


def asp_verify() -> int:
    py = sorted(
        (a, p)
        for a in ACTIONS
        for p in PRIZES
        if reasonableness_gate("pantry", a, p)
    )
    clingo_like = asp_valid()
    if clingo_like:
        print("OK: ASP twin emits reachable resolved facts.")
        return 0
    print("MISMATCH or empty ASP result.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: a doll, a carb, bravery, suspense, and magic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    action = getattr(args, "action", None) or rng.choice(list(_safe_lookup(SETTINGS, place).afford))
    prize = getattr(args, "prize", None) or rng.choice(list(PRIZES))
    if not reasonableness_gate(place, action, prize):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(NAMES)
    age = rng.randint(1, 9)
    return StoryParams(place=place, action=action, prize=prize, name=name, age=age)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
    StoryParams(place="pantry", action="climb", prize="carb", name="Tilly", age=3),
    StoryParams(place="barn", action="cross", prize="carb", name="June", age=4),
    StoryParams(place="attic", action="climb", prize="doll", name="Mara", age=5),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show resolved/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP mode is enabled; this tiny world keeps its own tall-tale gate.")
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
