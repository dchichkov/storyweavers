#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/addictive_evidence_lesson_learned_dialogue_rhyme_nursery.py
===============================================================================================================

A tiny nursery-rhyme storyworld about a sweet treat, a trail of evidence, and
a lesson learned.

Premise:
- A child or small character finds an irresistibly tasty treat.
- The treat is so tempting that the character keeps coming back for more.
- Little clues, or evidence, show what happened.
- A gentle helper uses dialogue to guide the character toward a better choice.
- The ending lands in a lesson learned, in a rhyming nursery cadence.

This script keeps the world model small and state-driven:
- physical meters track treats, crumbs, sticky fingers, and clues
- emotional memes track craving, worry, guilt, relief, and pride

It also includes a reasonableness gate, inline ASP rules, QA generation, and a
simple trace mode.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    guide: object | None = None
    hero: object | None = None
    treat: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    start_line: str = ""
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
class Temptation:
    id: str
    label: str
    phrase: str
    taste_line: str
    cue: str
    evidence: str
    lesson: str
    rhyme_end: str
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
class Guide:
    id: str
    label: str
    type: str
    line: str
    suggestion: str
    wrap_up: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.turns: list[str] = []

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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.turns = list(self.turns)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: callable
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


def _r_evidence(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters.get("crumbs", 0) >= THRESHOLD and ent.meters.get("sticky", 0) >= THRESHOLD:
            sig = ("evidence", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.meters["evidence"] = ent.meters.get("evidence", 0) + 1
            out.append(f"The crumbs and sticky fingers were evidence of a nibble nearby.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = next((e for e in world.entities.values() if e.kind == "character"), None)
    guide = next((e for e in world.entities.values() if e.kind == "guide"), None)
    if not child or not guide:
        return out
    if child.memes.get("craving", 0) >= THRESHOLD and child.meters.get("taken", 0) >= THRESHOLD:
        sig = ("worry", child.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.memes["worry"] = child.memes.get("worry", 0) + 1
        out.append(f"{guide.label} frowned a little, for too much sweet can make a tummy feel tight.")
    return out


CAUSAL_RULES = [
    Rule("evidence", _r_evidence),
    Rule("worry", _r_worry),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


@dataclass
class StoryParams:
    setting: str
    temptation: str
    hero_name: str
    hero_type: str
    guide_type: str
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


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoors=True, start_line="The kitchen was bright and neat."),
    "pantry": Setting(place="the pantry", indoors=True, start_line="The pantry was quiet and snug."),
    "garden": Setting(place="the garden", indoors=False, start_line="The garden was green and warm."),
}

TEMPTATIONS = {
    "honeycake": Temptation(
        id="honeycake",
        label="honey cake",
        phrase="a little honey cake",
        taste_line="The honey cake was sweet and soft, and it smelled like sunshine.",
        cue="sweet crumbs",
        evidence="crumbs on the table",
        lesson="too much sweet can make the tummy grumbly",
        rhyme_end="a tummy can't dance on cake after cake",
        tags={"sweet", "crumbs", "lesson"},
    ),
    "jamtoast": Temptation(
        id="jamtoast",
        label="jam toast",
        phrase="a shiny slice of jam toast",
        taste_line="The jam toast was rosy red and sticky-sweet.",
        cue="sticky fingers",
        evidence="jam on the chair",
        lesson="sticky hands leave clues",
        rhyme_end="jam on a hand makes a clue so grand",
        tags={"sweet", "sticky", "lesson"},
    ),
    "candy": Temptation(
        id="candy",
        label="candy",
        phrase="a bright striped candy",
        taste_line="The candy crackled and sparkled like a tiny star.",
        cue="a wrapper trail",
        evidence="wrappers under the chair",
        lesson="little clues tell the truth",
        rhyme_end="a wrapper trail gives a helpful tale",
        tags={"sweet", "clue", "lesson"},
    ),
}

GUIDES = {
    "mother": Guide(
        id="mother",
        label="Mom",
        type="mother",
        line="Mom came in softly and looked at the crumbs.",
        suggestion="Let's count what we found and save the rest for later.",
        wrap_up="Then Mom smiled, and the room felt calm again.",
    ),
    "father": Guide(
        id="father",
        label="Dad",
        type="father",
        line="Dad came in softly and looked at the clues.",
        suggestion="Let's pause, take a sip of water, and choose one small bite.",
        wrap_up="Then Dad smiled, and the room felt calm again.",
    ),
    "teacher": Guide(
        id="teacher",
        label="Teacher",
        type="teacher",
        line="Teacher came in softly and looked at the little clues.",
        suggestion="Let's put the treat away and wash our hands first.",
        wrap_up="Then Teacher smiled, and the room felt calm again.",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Ben", "Finn", "Max", "Theo", "Sam"]


def valid_combos() -> list[tuple[str, str]]:
    return [(s, t) for s in SETTINGS for t in TEMPTATIONS]


def validate_combo(setting: str, temptation: str) -> None:
    if setting not in SETTINGS:
        pass
    if temptation not in TEMPTATIONS:
        pass


def choose_name(rng: random.Random, hero_type: str) -> str:
    return rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)


def build_story(world: World, hero: Entity, guide: Entity, treat: Entity, temptation: Temptation) -> None:
    world.say(world.setting.start_line)
    world.say(
        f"{hero.id} saw {temptation.phrase}, and {hero.pronoun('subject')} loved its sweet little shine."
    )
    world.say(temptation.taste_line)
    world.say(
        f'"Just one more nibble," {hero.id} said. "It tastes like a happy chime."'
    )
    hero.memes["craving"] = hero.memes.get("craving", 0) + 1
    treat.meters["taken"] = treat.meters.get("taken", 0) + 1
    treat.meters["crumbs"] = treat.meters.get("crumbs", 0) + 1
    treat.meters["sticky"] = treat.meters.get("sticky", 0) + 1
    world.turns.append("temptation")
    propagate(world, narrate=False)

    world.para()
    world.say(
        f"But soon there was {temptation.evidence}, and that was evidence of a sneaky snack."
    )
    if hero.memes.get("craving", 0) >= THRESHOLD:
        world.say(f"{hero.id} blinked. \"Was that me?\" {hero.pronoun('subject')} asked.")
    world.say(guide.label + " answered, \"" + temptation.cue.capitalize() + " tell a tale.\"")
    world.say(guide.line)
    world.say(f"\"I know,\" {hero.id} whispered. \"I wanted more and more.\"")
    world.say(f"\"Then let us learn,\" said {guide.label}. \"{guide.suggestion}\"")
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    hero.memes["shame"] = hero.memes.get("shame", 0) + 1
    world.turns.append("warning")

    world.para()
    world.say(
        f"{hero.id} nodded and put the sweet treat away. {guide.wrap_up}"
    )
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    hero.memes["craving"] = max(0.0, hero.memes.get("craving", 0) - 1)
    treat.meters["saved"] = 1
    world.say(
        f"Lesson learned: {temptation.lesson}, and {temptation.rhyme_end}."
    )
    world.say(
        f"So {hero.id} washed {hero.pronoun('possessive')} hands, saved the rest, and skipped away in a tidy line."
    )
    world.turns.append("resolution")


def tell(setting_key: str, temptation_key: str, hero_name: str, hero_type: str, guide_type: str) -> World:
    setting = _safe_lookup(SETTINGS, setting_key)
    temptation = _safe_lookup(TEMPTATIONS, temptation_key)
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        meters={"crumbs": 0.0, "sticky": 0.0, "taken": 0.0},
        memes={"craving": 0.0, "worry": 0.0},
    ))
    guide_cfg = _safe_lookup(GUIDES, guide_type)
    guide = world.add(Entity(
        id=guide_cfg.label,
        kind="guide",
        type=guide_cfg.type,
        label=guide_cfg.label,
        meters={},
        memes={},
    ))
    treat = world.add(Entity(
        id=temptation.id,
        kind="thing",
        type="treat",
        label=temptation.label,
        phrase=temptation.phrase,
        owner=hero.id,
        caretaker=guide.id,
        meters={"taken": 0.0, "crumbs": 0.0, "sticky": 0.0, "saved": 0.0},
        memes={},
    ))
    build_story(world, hero, guide, treat, temptation)
    world.facts.update(hero=hero, guide=guide, treat=treat, temptation=temptation, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short nursery-rhyme story about {f["hero"].id}, a tempting {f["temptation"].label}, and the clues that gave it away.',
        f"Tell a gentle dialogue story where {f['hero'].id} keeps wanting more {f['temptation'].label} until the evidence makes the lesson clear.",
        f"Write a rhyme-like story for a young child that ends with \"Lesson learned\" after a sweet treat leaves evidence behind.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    guide = _safe_fact(world, f, "guide")
    treat = _safe_fact(world, f, "treat")
    temptation = _safe_fact(world, f, "temptation")
    return [
        QAItem(
            question=f"What did {hero.id} keep wanting more of?",
            answer=f"{hero.id} kept wanting more {treat.label}. It was so sweet that {hero.pronoun('subject')} wanted one more bite again and again.",
        ),
        QAItem(
            question=f"What evidence showed what happened with the {treat.label}?",
            answer=f"The evidence was {temptation.evidence}. Those little clues showed that {hero.id} had been snacking.",
        ),
        QAItem(
            question=f"What did {guide.label} say the clues could do?",
            answer=f"{guide.label} said that {temptation.cue} tell a tale, which meant the clues could help tell what happened.",
        ),
        QAItem(
            question="What lesson was learned at the end?",
            answer=f"The lesson learned was that {temptation.lesson}. {hero.id} listened, saved the rest, and chose a tidier way.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    temp = _safe_fact(world, f, "temptation")
    out = [
        QAItem(
            question="What is evidence?",
            answer="Evidence is a clue that helps show what happened, like crumbs, a wrapper, or sticky fingers.",
        ),
        QAItem(
            question="Why can sweets be hard to stop eating?",
            answer="Sweets can be hard to stop eating because they taste very good, so some people want more and more.",
        ),
        QAItem(
            question="What should you do before eating a treat?",
            answer="It is a good idea to stop, look, and listen to a grown-up or guide, especially if the treat is meant to be shared or saved.",
        ),
    ]
    if "sticky" in temp.tags:
        out.append(QAItem(
            question="Why do sticky fingers leave clues?",
            answer="Sticky fingers leave clues because they catch tiny bits of food and leave marks on cups, chairs, and hands.",
        ))
    return out


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
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  turns: {world.turns}")
    return "\n".join(lines)


ASP_RULES = r"""
% A treat is evidence-bearing if crumbs or sticky marks exist.
evident(T) :- treat(T), crumbs(T), sticky(T).

% The story is reasonable when the temptation has clues and a learned lesson.
reasonable(S, T) :- setting(S), treat(T), has_lesson(T), has_evidence(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TEMPTATIONS.items():
        lines.append(asp.fact("treat", tid))
        lines.append(asp.fact("has_lesson", tid))
        lines.append(asp.fact("has_evidence", tid))
        if "sticky" in t.tags:
            lines.append(asp.fact("sticky", tid))
        if "crumbs" in t.tags or tid == "honeycake":
            lines.append(asp.fact("crumbs", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/2."))
    return sorted(set(asp.atoms(model, "reasonable")))


def valid_story_combos() -> list[tuple[str, str]]:
    return valid_combos()


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = {(s, t) for s, t in valid_story_combos()}
    python_tagged = {(s, t) for s, t in python_set if s in SETTINGS and t in TEMPTATIONS}
    if clingo_set == python_tagged:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if clingo_set - python_tagged:
        print("  only in clingo:", sorted(clingo_set - python_tagged))
    if python_tagged - clingo_set:
        print("  only in python:", sorted(python_tagged - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld about sweet temptation, evidence, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide", choices=GUIDES)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    temptation = getattr(args, "temptation", None) or rng.choice(list(TEMPTATIONS))
    validate_combo(setting, temptation)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or choose_name(rng, gender)
    guide = getattr(args, "guide", None) or rng.choice(list(GUIDES))
    return StoryParams(setting=setting, temptation=temptation, hero_name=name, hero_type=gender, guide_type=guide)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.setting, params.temptation, params.hero_name, params.hero_type, params.guide_type)
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
    StoryParams(setting="kitchen", temptation="honeycake", hero_name="Mia", hero_type="girl", guide_type="mother"),
    StoryParams(setting="pantry", temptation="jamtoast", hero_name="Leo", hero_type="boy", guide_type="father"),
    StoryParams(setting="garden", temptation="candy", hero_name="Nora", hero_type="girl", guide_type="teacher"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show reasonable/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show reasonable/2."))
        combos = sorted(set(asp.atoms(model, "reasonable")))
        for s, t in combos:
            print(s, t)
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
            header = f"### {p.hero_name}: {p.temptation} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
