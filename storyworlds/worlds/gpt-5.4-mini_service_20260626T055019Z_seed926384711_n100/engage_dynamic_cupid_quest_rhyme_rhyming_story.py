#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055019Z_seed926384711_n100/engage_dynamic_cupid_quest_rhyme_rhyming_story.py
==========================================================================================================

A small standalone storyworld for a rhyming tale about an engage moment,
a dynamic little cupid, and a gentle quest for the right rhyme.

The domain is intentionally compact:
- a hero wants to say something sweet
- Cupid worries the first try will sound flat
- the pair go on a quest to find a better rhyme
- the ending proves the words changed the mood

The prose is authored to read like a child's rhyming story, while the world
model keeps physical meters and emotional memes that drive the narration.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    indoors: bool
    affords: set[str]
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
class Quest:
    id: str
    title: str
    route: str
    rhyme_need: str
    risk: str
    keyword: str = "quest"
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


@dataclass
class Rhyme:
    id: str
    label: str
    phrase: str
    kind: str
    helps: str
    finish: str
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
class StoryParams:
    place: str
    quest: str
    rhyme: str
    name: str
    gender: str
    helper: str
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
        clone.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _mget(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _mset(ent: Entity, key: str, value: float) -> None:
    ent.memes[key] = value


def _pget(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _padd(ent: Entity, key: str, value: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + value


SETTINGS = {
    "garden": Setting(place="the garden", indoors=False, affords={"quest", "rhyme"}),
    "library": Setting(place="the library", indoors=True, affords={"rhyme"}),
    "bridge": Setting(place="the little bridge", indoors=False, affords={"quest"}),
}

QUESTS = {
    "moon_quest": Quest(
        id="moon_quest",
        title="Moonlit Quest",
        route="follow the moon path",
        rhyme_need="find a rhyme that feels bright and true",
        risk="the first line will sound stiff and shy",
        keyword="Quest",
    ),
    "rose_quest": Quest(
        id="rose_quest",
        title="Rose Quest",
        route="cross the rose path",
        rhyme_need="find a rhyme that feels sweet and neat",
        risk="the message will lose its spark",
        keyword="Quest",
    ),
}

RHYMES = {
    "light": Rhyme(
        id="light",
        label="light rhyme",
        phrase="a light, bright rhyme",
        kind="soft",
        helps="makes the message easy to sing",
        finish="with a smile",
    ),
    "spark": Rhyme(
        id="spark",
        label="spark rhyme",
        phrase="a sparkly rhyme",
        kind="glow",
        helps="makes the words feel alive",
        finish="with a twirl",
    ),
    "heart": Rhyme(
        id="heart",
        label="heart rhyme",
        phrase="a warm heart rhyme",
        kind="kind",
        helps="makes the words feel brave",
        finish="with a hug",
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Tia", "Nora", "Ivy", "Zoe"]
BOY_NAMES = ["Theo", "Finn", "Leo", "Owen", "Max", "Ben"]
HELPERS = ["cupid", "sprite", "muse"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for qid in setting.affords:
            for rid in RHYMES:
                combos.append((place, qid, rid))
    return combos


def story_title(q: Quest, r: Rhyme) -> str:
    return f"{q.title} and the {r.label}"


def reasonableness_gate(q: Quest, r: Rhyme) -> bool:
    return True if q and r else False


def setup_lines(hero: Entity, helper: Entity, quest: Quest, rhyme: Rhyme, place: str) -> list[str]:
    return [
        f"{hero.id} was a small {hero.type} with a brave little heart.",
        f"Dynamic {helper.label} Cupid fluttered in, quick as a spark, and said, \"Let's make this sweet and not too stark.\"",
        f"Their {quest.title.lower()} began at {place}, where {hero.id} wanted to engage the day with a careful rhyme.",
        f"They carried {rhyme.phrase}, because the right words can shine.",
    ]


def run_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    quest = _safe_lookup(QUESTS, params.quest)
    rhyme = _safe_lookup(RHYMES, params.rhyme)
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper = world.add(Entity(id="Cupid", kind="character", type=params.helper, label="dynamic Cupid"))

    hero.memes["hope"] = 1.0
    helper.memes["buzz"] = 1.0
    hero.memes["nervous"] = 1.0

    for line in setup_lines(hero, helper, quest, rhyme, setting.place):
        world.say(line)

    world.para()
    world.say(
        f"{hero.id} started the quest by walking {quest.route}, "
        f"but the first line sounded a bit flat and bent."
    )
    hero.memes["doubt"] = 1.0
    helper.memes["concern"] = 1.0
    world.say(
        f"\"That won't quite do,\" whispered dynamic Cupid. "
        f"\"We need a rhyme that can dance and glimmer in the blue.\""
    )

    world.para()
    world.say(
        f"So they searched the quiet place together, listening for a clue."
    )
    _padd(hero, "travel", 1.0)
    _padd(helper, "travel", 1.0)
    hero.memes["hope"] += 1.0

    if quest.id == "moon_quest":
        world.say(
            f"Under the moon, they found a line that shone like silver dew."
        )
    else:
        world.say(
            f"By the roses, they found a line that smelled like morning glue."
        )

    world.say(
        f"It matched the {rhyme.kind} of {rhyme.label}, and the words began to bloom."
    )

    world.para()
    hero.memes["doubt"] = 0.0
    hero.memes["joy"] = 1.0
    hero.memes["engage"] = 1.0
    helper.memes["joy"] = 1.0

    world.say(
        f"{hero.id} spoke the new rhyme aloud, and the room felt bright and new."
    )
    world.say(
        f"The message engaged the moment instead of bruising it, and the shy heart answered too."
    )
    world.say(
        f"At the end of the quest, {hero.id} smiled {rhyme.finish}, "
        f"and dynamic Cupid twirled with a proud \"Hooray for you!\""
    )

    world.facts = {
        "hero": hero,
        "helper": helper,
        "quest": quest,
        "rhyme": rhyme,
        "setting": setting,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    quest = _safe_fact(world, f, "quest")
    rhyme = _safe_fact(world, f, "rhyme")
    return [
        f'Write a short rhyming story about {hero.id} and dynamic Cupid on a {quest.keyword}.',
        f"Tell a child-friendly tale where a little {hero.type} needs a better rhyme before a big engage moment.",
        f'Write a simple story with the words "Quest" and "Rhyme" that ends in a happy, musical choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    quest = _safe_fact(world, f, "quest")
    rhyme = _safe_fact(world, f, "rhyme")
    setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who went on the {quest.title} with {hero.id}?",
            answer=f"{hero.id} went with dynamic Cupid, who hurried along like a tiny bright helper.",
        ),
        QAItem(
            question=f"What did they need during the {quest.keyword.lower()}?",
            answer=f"They needed {rhyme.phrase} so the words would sound warm, lively, and kind.",
        ),
        QAItem(
            question=f"Where did the story happen?",
            answer=f"It happened at {setting.place}, where the little quest could happen safely.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} feeling joyful, the rhyme sounding right, and dynamic Cupid smiling proudly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a special journey or mission to find something, solve something, or finish an important task.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a word sound that matches another word sound, like sing and spring.",
        ),
        QAItem(
            question="Who is Cupid in stories?",
            answer="Cupid is often a tiny helper from stories who connects hearts and helps with love.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) " + " ".join(bits))
    return "\n".join(lines)


@dataclass
class ASPStub:
    pass
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


ASP_RULES = r"""
% Declarative twin: a story is valid when a quest and rhyme exist together.
valid_story(P,Q,R) :- place(P), quest(Q), rhyme(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for r in RHYMES:
        lines.append(asp.fact("rhyme", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show valid_story/3.")
    model = asp.one_model(program)
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set((p, q, r) for p, q, r in valid_combos())
    if asp_set == py_set:
        print(f"OK: ASP matches Python ({len(py_set)} combos).")
        return 0
    print("MISMATCH")
    print("ASP-only:", sorted(asp_set - py_set))
    print("PY-only:", sorted(py_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld: engage, dynamic Cupid, Quest, Rhyme.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS, default="cupid")
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
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "quest", None):
        combos = [c for c in combos if c[1] == getattr(args, "quest", None)]
    if getattr(args, "rhyme", None):
        combos = [c for c in combos if c[2] == getattr(args, "rhyme", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, rhyme = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or "cupid"
    return StoryParams(place=place, quest=quest, rhyme=rhyme, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = run_world(params)
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
    StoryParams(place="garden", quest="moon_quest", rhyme="light", name="Mira", gender="girl", helper="cupid"),
    StoryParams(place="library", quest="moon_quest", rhyme="heart", name="Theo", gender="boy", helper="cupid"),
    StoryParams(place="bridge", quest="rose_quest", rhyme="spark", name="Lina", gender="girl", helper="cupid"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.quest} at {p.place} (rhyme: {p.rhyme})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
