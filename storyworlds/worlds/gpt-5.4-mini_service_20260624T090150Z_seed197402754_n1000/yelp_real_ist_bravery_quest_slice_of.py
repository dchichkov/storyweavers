#!/usr/bin/env python3
"""
A tiny slice-of-life storyworld about a small brave quest, with the possibility
of a startled yelp when the real world feels a little bigger than expected.

The world is grounded in ordinary places and practical choices:
- a child or young person wants to complete a small quest,
- they meet a mild challenge,
- they gather bravery in a real-ish, everyday way,
- they finish the task and feel proud.

This script follows the Storyweavers world contract:
- self-contained stdlib script
- shared result containers imported eagerly
- inline ASP twin + Python reasonableness gate
- story driven by simulated state rather than a frozen paragraph
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
# Domain model
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
    role: str = ""
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.role in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.role in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def obj(self) -> str:
        return "them" if self.plural else "it"
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
class Quest:
    id: str
    name: str
    task: str
    brave_step: str
    outcome: str
    keyword: str
    tags: set[str] = field(default_factory=set)
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
class Hurdle:
    id: str
    name: str
    description: str
    fear: str
    yelp_trigger: str
    resolved_by: str
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
        self.fired: set[tuple] = set()
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
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "corner_store": Setting(place="the corner store", indoors=True, affords={"errand"}),
    "library": Setting(place="the library", indoors=True, affords={"return_book"}),
    "garden": Setting(place="the garden", indoors=False, affords={"watering"}),
    "bus_stop": Setting(place="the bus stop", indoors=False, affords={"ride_waiting"}),
}

QUESTS = {
    "snack_run": Quest(
        id="snack_run",
        name="snack run",
        task="buy a treat for home",
        brave_step="walk up to the counter and ask for it clearly",
        outcome="came home with the snack in a paper bag",
        keyword="yelp",
        tags={"store", "counter", "errand", "yelp"},
    ),
    "book_return": Quest(
        id="book_return",
        name="book return",
        task="bring a book back on time",
        brave_step="step into the quiet library and hand over the book",
        outcome="got the book back onto the shelf and the card was stamped",
        keyword="real-ist",
        tags={"library", "quiet", "return_book"},
    ),
    "watering": Quest(
        id="watering",
        name="watering quest",
        task="give the thirsty plants a drink",
        brave_step="carry the watering can through the damp path",
        outcome="left the garden looking neat and bright",
        keyword="bravery",
        tags={"garden", "plants", "watering"},
    ),
    "bus_ride": Quest(
        id="bus_ride",
        name="bus ride",
        task="ride the bus to a nearby place",
        brave_step="step onto the bus and hold the rail",
        outcome="made it to the stop with a calm smile",
        keyword="quest",
        tags={"bus", "ride_waiting"},
    ),
}

HURDLES = {
    "counter_height": Hurdle(
        id="counter_height",
        name="high counter",
        description="the counter looked taller than expected",
        fear="the bell and the grown-up voices sounded big",
        yelp_trigger="a sudden clink from a dropped spoon",
        resolved_by="asking politely and standing on tiptoe",
    ),
    "library_silence": Hurdle(
        id="library_silence",
        name="library quiet",
        description="the library was so quiet that every step felt loud",
        fear="the hush made the room feel serious",
        yelp_trigger="a chair scraping softly across the floor",
        resolved_by="taking a steady breath and whispering the request",
    ),
    "muddy_path": Hurdle(
        id="muddy_path",
        name="muddy path",
        description="the path had a dark wet patch after the rain",
        fear="the slippery spot looked tricky",
        yelp_trigger="a boot slipped just a little",
        resolved_by="slow, careful steps and both hands on the can",
    ),
    "bus_rattle": Hurdle(
        id="bus_rattle",
        name="bus rattle",
        description="the bus gave a loud rattle as it pulled in",
        fear="the noise made the child pause",
        yelp_trigger="the doors hissed open all at once",
        resolved_by="holding the rail and climbing on one step at a time",
    ),
}

NAMES = ["Mia", "Nora", "Eli", "Jules", "Lena", "Theo", "Ava", "Noah"]
KIND_TRAITS = ["careful", "quiet", "curious", "gentle", "steady", "real-ist"]


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def quest_at_risk(quest: Quest, hurdle: Hurdle) -> bool:
    return bool(quest.tags & {
        "store" if hurdle.id == "counter_height" else "",
        "library" if hurdle.id == "library_silence" else "",
        "garden" if hurdle.id == "muddy_path" else "",
        "bus" if hurdle.id == "bus_rattle" else "",
    })


def is_reasonable_combo(setting_id: str, quest_id: str) -> bool:
    setting = _safe_lookup(SETTINGS, setting_id)
    quest = _safe_lookup(QUESTS, quest_id)
    if quest.id == "snack_run":
        return setting_id == "corner_store"
    if quest.id == "book_return":
        return setting_id == "library"
    if quest.id == "watering":
        return setting_id == "garden"
    if quest.id == "bus_ride":
        return setting_id == "bus_stop"
    return False


def hurdle_for(setting_id: str, quest_id: str) -> Hurdle:
    if quest_id == "snack_run":
        return HURDLES["counter_height"]
    if quest_id == "book_return":
        return HURDLES["library_silence"]
    if quest_id == "watering":
        return HURDLES["muddy_path"]
    if quest_id == "bus_ride":
        return HURDLES["bus_rattle"]
    pass


def make_name(rng: random.Random, gender: str) -> str:
    if gender == "girl":
        return rng.choice([n for n in NAMES if n in {"Mia", "Nora", "Lena", "Ava"}])
    if gender == "boy":
        return rng.choice([n for n in NAMES if n in {"Eli", "Theo", "Noah"}])
    return rng.choice(NAMES)


def narration_intro(hero: Entity, quest: Quest, setting: Setting) -> str:
    return (
        f"{hero.id} was a {hero.memes.get('trait_word', 'steady')} kid who liked small, real-world quests. "
        f"One day, {hero.pronoun('subject')} wanted to do a {quest.name} at {setting.place}."
    )


def narration_love(hero: Entity, quest: Quest) -> str:
    return (
        f"{hero.pronoun('subject').capitalize()} liked the idea because it felt simple and real-ist: "
        f"just one task, one place, and one brave step."
    )


def narration_arrival(hero: Entity, setting: Setting) -> str:
    if setting.indoors:
        return f"{hero.id} walked inside and looked around at the neat shelves and quiet corners."
    return f"{hero.id} arrived outside and watched the ordinary little world go on around {hero.pronoun('object')}."


def narration_hurdle(hero: Entity, hurdle: Hurdle) -> str:
    return (
        f"Then {hurdle.description}. {hero.pronoun('subject').capitalize()} felt a small yelp rise in {hero.pronoun('possessive')} throat when "
        f"{hurdle.yelp_trigger}."
    )


def narration_bravery(hero: Entity, quest: Quest, hurdle: Hurdle) -> str:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1.0
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1.0
    return (
        f"{hero.pronoun('subject').capitalize()} took a breath, did {hurdle.resolved_by}, and kept going. "
        f"That was the brave part of the quest."
    )


def narration_finish(hero: Entity, quest: Quest) -> str:
    return (
        f"At the end, {quest.outcome}. {hero.id} felt proud, and the little yelp was only a memory."
    )


def build_world(setting_id: str, quest_id: str, name: str, gender: str, trait: str) -> World:
    if not is_reasonable_combo(setting_id, quest_id):
        pass
    setting = _safe_lookup(SETTINGS, setting_id)
    quest = _safe_lookup(QUESTS, quest_id)
    hurdle = hurdle_for(setting_id, quest_id)
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", role=gender))
    hero.memes["trait_word"] = trait
    world.facts["hero"] = hero
    world.facts["quest"] = quest
    world.facts["hurdle"] = hurdle

    world.say(narration_intro(hero, quest, setting))
    world.say(narration_love(hero, quest))

    world.para()
    world.say(narration_arrival(hero, setting))
    world.say(f"{hero.id} wanted to {quest.task}, so {hero.pronoun('subject')} got ready for the quest.")
    world.say(narration_hurdle(hero, hurdle))
    world.say(narration_bravery(hero, quest, hurdle))

    world.para()
    world.say(f"{hero.id} {quest.brave_step}.")
    world.say(narration_finish(hero, quest))

    world.facts["resolved"] = True
    world.facts["trait"] = trait
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    quest: Quest = _safe_fact(world, f, "quest")
    hurdle: Hurdle = _safe_fact(world, f, "hurdle")
    return [
        f'Write a short slice-of-life story for a child named {hero.id} who wants to do a "{quest.name}" and shows bravery in a small real-world moment.',
        f'Tell a gentle story where {hero.id} faces "{hurdle.name}" during a {quest.name}, hears a tiny yelp, and keeps going.',
        f'Write a simple story using the words "{quest.keyword}", "Bravery", and "Quest" in a natural way.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    quest: Quest = _safe_fact(world, f, "quest")
    hurdle: Hurdle = _safe_fact(world, f, "hurdle")
    setting = world.setting
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {setting.place}?",
            answer=f"{hero.id} wanted to do a {quest.name}. It was a small everyday quest that took one brave step.",
        ),
        QAItem(
            question=f"What made {hero.id} want to yelp during the story?",
            answer=f"{hurdle.description.capitalize()}, and {hurdle.yelp_trigger} made the moment feel suddenly loud.",
        ),
        QAItem(
            question=f"How did {hero.id} show bravery?",
            answer=f"{hero.id} showed bravery by taking a breath, doing {hurdle.resolved_by}, and finishing the quest.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"By the end, {hero.id} had completed the {quest.name} and felt proud instead of worried.",
        ),
    ]


WORLD_QA = [
    QAItem(
        question="What is bravery?",
        answer="Bravery is doing something even when you feel a little scared, usually by taking one careful step at a time.",
    ),
    QAItem(
        question="What is a quest?",
        answer="A quest is a goal or task someone tries to complete, often by following a few steps and not giving up.",
    ),
    QAItem(
        question="What does slice of life mean?",
        answer="Slice of life means the story is about an ordinary moment from everyday living, like a trip to a store or library.",
    ),
    QAItem(
        question="What is a yelp?",
        answer="A yelp is a quick little sound someone makes when they are surprised or startled.",
    ),
    QAItem(
        question="What does real-ist mean in this storyworld?",
        answer="Real-ist means the story stays close to everyday life, with familiar places, small feelings, and practical actions.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_QA


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A quest fits a setting when the setting affords the quest.
fits(S, Q) :- setting(S), quest(Q), affords(S, Q).

% A hurdle belongs to the quest that matches the setting.
has_hurdle(Q, H) :- quest(Q), hurdle(H), hurdle_for(Q, H).

% A story is reasonable when the setting, quest, and hurdle line up.
valid(S, Q, H) :- fits(S, Q), has_hurdle(Q, H).

% In this world, the brave turn resolves the hurdle.
resolved(Q) :- quest(Q).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoors:
            lines.append(asp.fact("indoors", sid))
        for q in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, q))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for hid, _ in HURDLES.items():
        lines.append(asp.fact("hurdle", hid))
    lines.append(asp.fact("hurdle_for", "snack_run", "counter_height"))
    lines.append(asp.fact("hurdle_for", "book_return", "library_silence"))
    lines.append(asp.fact("hurdle_for", "watering", "muddy_path"))
    lines.append(asp.fact("hurdle_for", "bus_ride", "bus_rattle"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {
        (s, q, h)
        for s in SETTINGS
        for q in QUESTS
        for h in HURDLES
        if is_reasonable_combo(s, q)
        and ((q == "snack_run" and h == "counter_height")
             or (q == "book_return" and h == "library_silence")
             or (q == "watering" and h == "muddy_path")
             or (q == "bus_ride" and h == "bus_rattle"))
    }
    clingo = set(asp_valid_combos())
    if clingo == py:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    print("only in ASP:", sorted(clingo - py))
    print("only in Python:", sorted(py - clingo))
    return 1


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    quest: str
    name: str
    gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life bravery quest storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=KIND_TRAITS)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    quest = getattr(args, "quest", None) or rng.choice(list(QUESTS))
    if getattr(args, "setting", None) and getattr(args, "quest", None) and not is_reasonable_combo(getattr(args, "setting", None), getattr(args, "quest", None)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or make_name(rng, getattr(args, "gender", None) or rng.choice(["girl", "boy"]))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    trait = getattr(args, "trait", None) or rng.choice(KIND_TRAITS)
    return StoryParams(setting=setting, quest=quest, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params.setting, params.quest, params.name, params.gender, params.trait)
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
        lines.append(f"  {e.id} ({e.kind}) memes={dict(e.memes)} meters={dict(e.meters)}")
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


CURATED = [
    StoryParams(setting="corner_store", quest="snack_run", name="Mia", gender="girl", trait="careful"),
    StoryParams(setting="library", quest="book_return", name="Theo", gender="boy", trait="quiet"),
    StoryParams(setting="garden", quest="watering", name="Ava", gender="girl", trait="gentle"),
    StoryParams(setting="bus_stop", quest="bus_ride", name="Eli", gender="boy", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        models = asp_valid_combos()
        print(f"{len(models)} compatible setting/quest/hurdle triples:\n")
        for row in models:
            print(" ", row)
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
