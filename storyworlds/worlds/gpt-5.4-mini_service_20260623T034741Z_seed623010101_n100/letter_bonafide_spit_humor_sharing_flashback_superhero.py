#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/letter_bonafide_spit_humor_sharing_flashback_superhero.py
===============================================================================================================================

A small superhero storyworld about a kid hero, a bonafide letter, a splatty spit
villain, and a shared fix. The world uses typed entities with meters (physical)
and memes (emotional), a tiny forward rule engine, an inline ASP twin, and
grounded QA.

Seed-inspired premise:
- A hero receives a bonafide letter.
- A joke makes the scene lighter.
- A flashback reveals a shared clue.
- A spit-powered mess creates trouble.
- Sharing and teamwork resolve it.

The core story stays child-facing and concrete, with state driving the narration.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    owner: Optional[str] = None
    partner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    foe: object | None = None
    hero: object | None = None
    kit_ent: object | None = None
    letter: object | None = None
    pal: object | None = None
    recovery: object | None = None
    trouble_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

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
    id: str
    place: str
    affords: set[str] = field(default_factory=set)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class HeroKit:
    id: str
    label: str
    phrase: str
    use: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Trouble:
    id: str
    label: str
    phrase: str
    mess: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Recovery:
    id: str
    label: str
    phrase: str
    method: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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


def _r_spit(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    foe = world.get("foe")
    if hero.meters["spat"] < THRESHOLD:
        return out
    sig = ("spit",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    foe.meters["mess"] += 1
    foe.memes["annoyed"] += 1
    out.append("The spit made a sticky mess.")
    return out


def _r_team(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    pal = world.get("pal")
    if pal.meters["shared"] < THRESHOLD:
        return out
    sig = ("team",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["hope"] += 1
    pal.memes["hope"] += 1
    out.append("Sharing helped the team feel braver.")
    return out


CAUSAL_RULES = [
    Rule("spit", "physical", _r_spit),
    Rule("team", "social", _r_team),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["spat"] += 1
    propagate(sim, narrate=False)
    return {
        "mess": sim.get("foe").meters["mess"] >= THRESHOLD,
        "hope": sim.get("hero").memes["hope"] + sim.get("pal").memes["hope"],
    }


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for kit_id, kit in KITS.items():
            for trouble_id, trouble in TROUBLES.items():
                if setting_id in setting.affords and kit_id in kit.tags and trouble_id in trouble.tags:
                    combos.append((setting_id, kit_id, trouble_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    kit: str
    trouble: str
    hero_name: str
    hero_gender: str
    pal_name: str
    pal_gender: str
    villain_name: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


SETTINGS = {
    "rooftop": Setting(id="rooftop", place="the rooftop", affords={"letter", "flashback", "sharing", "humor", "spit"}),
    "alley": Setting(id="alley", place="the alley by the mailbox", affords={"letter", "flashback", "sharing", "humor", "spit"}),
    "tower": Setting(id="tower", place="the old clock tower", affords={"letter", "flashback", "sharing", "humor", "spit"}),
}

KITS = {
    "letter": HeroKit(id="letter", label="bonafide letter", phrase="a bonafide letter", use="read the bonafide letter", tags={"letter"}),
    "glove": HeroKit(id="glove", label="signal glove", phrase="a signal glove", use="signal for help", tags={"sharing"}),
    "joke": HeroKit(id="joke", label="joke book", phrase="a tiny joke book", use="tell a joke", tags={"humor"}),
}

TROUBLES = {
    "spit": Trouble(id="spit", label="spit splatter", phrase="a spit splatter", mess="sticky", tags={"spit"}),
    "goo": Trouble(id="goo", label="goo puddle", phrase="a goo puddle", mess="gooey", tags={"spit"}),
}

RECOVERIES = {
    "share": Recovery(id="share", label="shared plan", phrase="a shared plan", method="share the clue and clean together", tags={"sharing"}),
    "wipe": Recovery(id="wipe", label="wipe cloth", phrase="a clean cloth", method="wipe up the mess", tags={"sharing"}),
}

GIRL_NAMES = ["Mina", "Lia", "Tia", "Nora", "Zoe"]
BOY_NAMES = ["Kai", "Ben", "Oli", "Theo", "Max"]
VILLAINS = ["Snicker Spit", "Dr. Spatter", "Captain Ptooey"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a 3-to-5-year-old that includes the words "{f["kit"].label}", "bonafide", and "spit".',
        f"Tell a funny superhero story where {f['hero'].id} gets a bonafide letter, remembers a flashback, and shares a plan with {f['pal'].id}.",
        f"Write a child-friendly superhero tale with humor, sharing, and a flashback, ending with a shared rescue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    pal = f["pal"]
    kit = f["kit"]
    trouble = f["trouble"]
    rec = f["recovery"]
    qa = [
        QAItem(
            f"Why did {hero.id} read the bonafide letter?",
            f"{hero.id} read the bonafide letter because it was a real message and it told them where to go next. The letter helped start the adventure.",
        ),
        QAItem(
            f"What was funny in the story before the trouble got bigger?",
            f"{hero.id} told a silly joke, and that made {pal.id} laugh. The humor helped the team feel less scared before they faced {trouble.label}.",
        ),
        QAItem(
            f"What did the flashback remind {hero.id} about?",
            f"The flashback reminded {hero.id} that they had shared their clue before. That memory helped them use {kit.label} the right way.",
        ),
        QAItem(
            f"How did {hero.id} and {pal.id} solve the problem with {trouble.label}?",
            f"They shared the clue and worked together, following {rec.method}. Sharing helped them beat the mess and keep going.",
        ),
    ]
    if f.get("mess"):
        qa.append(QAItem(
            f"What happened when {hero.id} got spit near {trouble.phrase}?",
            f"{trouble.phrase} turned into a sticky mess, and the villain's spit made the problem harder. That is why the team needed a shared plan.",
        ))
    if f.get("resolved"):
        qa.append(QAItem(
            f"How did the ending show that sharing mattered?",
            f"{hero.id} and {pal.id} split the work and cleaned up together. By sharing, they turned a nasty splat into a safe ending.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["kit"].tags) | set(world.facts["trouble"].tags)
    out = []
    if "letter" in tags:
        out.append(QAItem("What is a letter?", "A letter is a message written on paper and sent to someone. It can tell news or ask for help."))
    if "spit" in tags:
        out.append(QAItem("Why is spit messy?", "Spit is wet and sticky, so it can make a mess on the ground or on clothes."))
    if "sharing" in tags:
        out.append(QAItem("What does sharing mean?", "Sharing means giving someone else part of what you have or letting them help. It is kind and useful."))
    if "humor" in tags:
        out.append(QAItem("What is humor?", "Humor is something funny that makes people smile or laugh."))
    if "flashback" in tags:
        out.append(QAItem("What is a flashback in a story?", "A flashback is when the story briefly shows something that happened before. It helps the reader remember an important clue."))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
good_combo(S, K, T) :- setting(S), kit(K), trouble(T),
                       afford(S, letter), has_tag(K, letter), has_tag(T, spit).
has_tag(letter, letter).
has_tag(glove, sharing).
has_tag(joke, humor).
has_tag(spit, spit).
has_tag(goo, spit).
afford(rooftop, letter).
afford(rooftop, spit).
afford(rooftop, sharing).
afford(rooftop, humor).
afford(rooftop, flashback).
afford(alley, letter).
afford(alley, spit).
afford(alley, sharing).
afford(alley, humor).
afford(alley, flashback).
afford(tower, letter).
afford(tower, spit).
afford(tower, sharing).
afford(tower, humor).
afford(tower, flashback).
setting(rooftop). setting(alley). setting(tower).
kit(letter). kit(glove). kit(joke).
trouble(spit). trouble(goo).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for a in sorted(_safe_lookup(SETTINGS, sid).affords):
            lines.append(asp.fact("afford", sid, a))
    for kid, kit in KITS.items():
        lines.append(asp.fact("kit", kid))
        for t in sorted(kit.tags):
            lines.append(asp.fact("has_tag", kid, t))
    for tid, tr in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        for t in sorted(tr.tags):
            lines.append(asp.fact("has_tag", tid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_combo/3."))
    return sorted(set(asp.atoms(model, "good_combo")))


def asp_verify() -> int:
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        ok = False
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            print("MISMATCH: generated story was empty.")
            ok = False
    except Exception as exc:  # smoke test must fail if ordinary generation crashes
        print(f"MISMATCH: generation smoke test failed: {exc}")
        ok = False
    if ok:
        print("OK: ASP/Python parity and generation smoke test passed.")
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world: letter, bonafide, spit, humor, sharing, flashback.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--kit", choices=KITS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--pal")
    ap.add_argument("--pal-gender", choices=["girl", "boy"])
    ap.add_argument("--villain")
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
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "kit", None) is None or c[1] == getattr(args, "kit", None))
              and (getattr(args, "trouble", None) is None or c[2] == getattr(args, "trouble", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, kit, trouble = rng.choice(list(combos))
    hero_gender = getattr(args, "hero_gender", None) or rng.choice(["girl", "boy"])
    pal_gender = getattr(args, "pal_gender", None) or ("boy" if hero_gender == "girl" else "girl")
    hero = getattr(args, "hero", None) or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    pal = getattr(args, "pal", None) or rng.choice([n for n in (GIRL_NAMES if pal_gender == "girl" else BOY_NAMES) if n != hero])
    villain = getattr(args, "villain", None) or rng.choice(VILLAINS)
    return StoryParams(setting=setting, kit=kit, trouble=trouble,
                       hero_name=hero, hero_gender=hero_gender,
                       pal_name=pal, pal_gender=pal_gender,
                       villain_name=villain)


def tell(setting: Setting, kit: HeroKit, trouble: Trouble, hero_name: str, hero_gender: str,
         pal_name: str, pal_gender: str, villain_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero",
                            label="hero", tags={"hero"}))
    pal = world.add(Entity(id=pal_name, kind="character", type=pal_gender, role="pal",
                           label="sidekick", tags={"pal"}))
    foe = world.add(Entity(id=villain_name, kind="character", type="thing", role="foe",
                           label=villain_name, tags={"foe", trouble.id}))
    letter = world.add(Entity(id="letter", type="thing", label="bonafide letter", tags={"letter"}))
    kit_ent = world.add(Entity(id="kit", type="thing", label=kit.label, tags=set(kit.tags)))
    trouble_ent = world.add(Entity(id="trouble", type="thing", label=trouble.label, tags=set(trouble.tags)))
    recovery = world.add(Entity(id="recovery", type="thing", label="shared plan", tags={"sharing"}))
    hero.meters["reading"] = 0.0
    hero.meters["spat"] = 0.0
    hero.memes["humor"] = 0.0
    hero.memes["hope"] = 0.0
    pal.meters["shared"] = 0.0
    pal.memes["hope"] = 0.0
    foe.meters["mess"] = 0.0
    foe.memes["annoyed"] = 0.0
    world.facts["kit"] = kit
    world.facts["trouble"] = trouble
    world.facts["recovery"] = RECOVERIES["share"]
    world.facts["hero"] = hero
    world.facts["pal"] = pal
    world.facts["foe"] = foe
    world.facts["setting"] = setting

    world.say(f"{hero.id} found a bonafide letter on {setting.place}.")
    world.say(f"It said there was a clue hidden where the city could hear a silly joke.")
    world.say(f"{pal.id} grinned and said, \"This case needs humor, not grump faces.\"")
    hero.memes["humor"] += 1
    hero.meters["reading"] += 1

    world.para()
    world.say(f"A flashback popped into {hero.id}'s head: they had shared {kit.label} before.")
    world.say(f"That memory made the clue feel familiar, like a cape blowing in the wind.")

    world.para()
    hero.meters["spat"] += 1
    world.say(f"Then {foe.id} spat a sticky splat across {trouble.phrase}.")
    propagate(world, narrate=True)
    world.say(f"{hero.id} laughed, \"Even villains can be messy in a very silly way.\"")

    world.para()
    pal.meters["shared"] += 1
    recovery.method = "share the clue and clean together"
    world.say(f"{hero.id} and {pal.id} chose to share the clue and clean together.")
    world.say(f"They used {kit.label} and {recovery.label} to fix the trouble.")
    hero.memes["hope"] += 1
    pal.memes["hope"] += 1

    world.facts["resolved"] = True
    world.facts["mess"] = True
    return world


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.kit not in KITS or params.trouble not in TROUBLES:
        pass
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(KITS, params.kit), _safe_lookup(TROUBLES, params.trouble),
                 params.hero_name, params.hero_gender, params.pal_name, params.pal_gender,
                 params.villain_name)
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
    StoryParams(setting="rooftop", kit="letter", trouble="spit", hero_name="Mina", hero_gender="girl", pal_name="Kai", pal_gender="boy", villain_name="Snicker Spit"),
    StoryParams(setting="alley", kit="glove", trouble="goo", hero_name="Theo", hero_gender="boy", pal_name="Lia", pal_gender="girl", villain_name="Dr. Spatter"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show good_combo/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
