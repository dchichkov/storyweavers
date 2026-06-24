#!/usr/bin/env python3
"""
A small mythic storyworld about a rupture, a test of bravery, and the repair
that follows.

The seed premise:
- A sacred path is split by a sudden rupture.
- A young hero must cross it to help the village.
- Bravery is not loudness; it is choosing the hard step while fear is present.
- The story ends when the hero mends the break and changes how the world feels.

The world model tracks:
- physical meters: width of the rupture, height of the barrier, gathered tools,
  soot, light, repaired stone, safe passage
- emotional memes: fear, resolve, hope, honor, trust, pride

The story is generated from state transitions, not a frozen paragraph.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    hero: object | None = None
    rift: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "mother", "priestess"}
        male = {"boy", "king", "father", "priest", "smith"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    place: str = "the stone bridge"
    legend: str = ""
    sanctum: bool = False
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
class Trial:
    id: str
    noun: str
    verb: str
    danger: str
    measure: str
    zone: str
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
class Remedy:
    id: str
    label: str
    phrase: str
    covers: str
    guards: set[str]
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
        self.trace: list[str] = []

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
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


def emit_state_change(world: World, msg: str) -> None:
    world.trace.append(msg)


def _r_fear_to_resolve(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes.get("fear", 0.0) < THRESHOLD:
            continue
        if e.memes.get("resolve", 0.0) < THRESHOLD:
            continue
        sig = ("bravery", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["bravery"] = e.memes.get("bravery", 0.0) + 1
        out.append(f"{e.id} found bravery inside the fear.")
    return out


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    rift = world.entities.get("rift")
    remedy = world.entities.get("remedy")
    if not hero or not rift:
        return out
    if hero.memes.get("bravery", 0.0) < THRESHOLD:
        return out
    if world.fired and ("repair", hero.id) in world.fired:
        return out
    if remedy is None:
        return out
    if hero.meters.get("tools", 0.0) < THRESHOLD:
        return out
    sig = ("repair", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    rift.meters["width"] = max(0.0, rift.meters.get("width", 0.0) - 1.0)
    rift.meters["cracked"] = max(0.0, rift.meters.get("cracked", 0.0) - 1.0)
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    out.append("The break was narrowed by careful hands and a steady heart.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_fear_to_resolve, _r_repair):
            out = rule(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "bridge": Setting(
        place="the stone bridge",
        legend="an old road of kings crossed the river there",
        affords={"cross", "repair"},
        sanctum=False,
    ),
    "temple": Setting(
        place="the moon temple",
        legend="the moon priests once lit the stairs with silver oil",
        affords={"descend", "repair"},
        sanctum=True,
    ),
    "cliff": Setting(
        place="the cliff path",
        legend="wind and thunder had carved the path for ages",
        affords={"cross", "repair"},
        sanctum=False,
    ),
}

TRIALS = {
    "chasm": Trial(
        id="chasm",
        noun="chasm",
        verb="cross the gap",
        danger="falling",
        measure="wide and dark",
        zone="feet",
        keyword="rupture",
        tags={"rupture", "stone"},
    ),
    "rift": Trial(
        id="rift",
        noun="rift",
        verb="step onto the broken span",
        danger="shaking loose stones",
        measure="split and jagged",
        zone="feet",
        keyword="rupture",
        tags={"rupture", "stone"},
    ),
}

REMEDIES = {
    "rope": Remedy(
        id="rope",
        label="a rope bridge",
        phrase="a woven rope bridge",
        covers="feet",
        guards={"falling"},
        prep="gather reeds and tie a rope bridge",
        tail="laid the rope bridge across the gap",
    ),
    "stones": Remedy(
        id="stones",
        label="steady stones",
        phrase="a line of steady stones",
        covers="feet",
        guards={"shaking"},
        prep="carry steady stones from the riverbank",
        tail="placed the stones where the path had split",
    ),
    "torch": Remedy(
        id="torch",
        label="a torch",
        phrase="a bright torch of pine and oil",
        covers="hands",
        guards={"dark"},
        prep="light a torch for the dark way",
        tail="held the torch while the path was made safe",
    ),
}

HEROES = [
    ("Ari", "boy"),
    ("Mira", "girl"),
    ("Niko", "boy"),
    ("Sela", "girl"),
    ("Tavi", "boy"),
]

ADJECTIVES = ["young", "steady", "curious", "quiet", "brave", "small"]


@dataclass
class StoryParams:
    setting: str
    trial: str
    remedy: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_name, setting in SETTINGS.items():
        for t_name, trial in TRIALS.items():
            if "repair" not in setting.affords:
                continue
            for r_name, remedy in REMEDIES.items():
                if trial.noun == "chasm" and remedy.id == "rope":
                    combos.append((s_name, t_name, r_name))
                elif trial.noun == "rift" and remedy.id in {"stones", "rope"}:
                    combos.append((s_name, t_name, r_name))
    return combos


def place_sentence(setting: Setting, trial: Trial) -> str:
    return f"{setting.place.capitalize()} stood beneath an old legend: {setting.legend}."


def intro(world: World, hero: Entity, elder: Entity) -> None:
    world.say(
        f"{hero.id} was a {next(t for t in hero.memes if False),}"
    )


def tell(setting: Setting, trial: Trial, remedy: Remedy, hero_name: str, hero_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name))
    elder = world.add(Entity(id="elder", kind="character", type="priest", label="the elder"))
    rift = world.add(Entity(id="rift", type="thing", label=trial.noun, meters={"width": 2.0, "cracked": 1.0}))
    tool = world.add(Entity(id="remedy", type="thing", label=remedy.label, phrase=remedy.phrase, owner=hero.id))
    hero.memes.update({"fear": 0.0, "resolve": 0.0, "bravery": 0.0, "hope": 0.0, "trust": 0.0})
    world.facts.update(hero=hero, elder=elder, rift=rift, remedy=tool, trial=trial, setting=setting, remedy_cfg=remedy)

    world.say(f"Long ago, {hero_name} was a {trait} {hero_type} who lived by {setting.place}.")
    world.say(place_sentence(setting, trial))
    world.say(
        f"Each dawn, the people looked at the {trial.noun}, because the path was {trial.measure} and the river ran under it."
    )
    world.para()
    world.say(
        f"{hero_name} loved the old road, but {hero_name} also knew the {trial.noun} was dangerous."
    )
    hero.memes["fear"] += 1
    world.say(
        f"{hero_name}'s {trait} heart trembled, yet {hero.pronoun()} listened when {elder.label} said that bravery could walk with fear."
    )
    world.para()
    world.say(
        f"Then {hero_name} chose to {trial.verb}, carrying {remedy.phrase}."
    )
    hero.meters["tools"] += 1
    hero.memes["resolve"] += 1
    propagate(world, narrate=True)
    world.say(
        f"{hero_name} used {remedy.prep}, because {trial.danger} was the worst danger there."
    )
    world.para()
    hero.memes["fear"] += 1
    hero.memes["resolve"] += 1
    hero.memes["trust"] += 1
    hero.memes["bravery"] += 1
    world.say(
        f"With a steady breath, {hero_name} did not turn away from the rupture."
    )
    world.say(
        f"{hero_name} kept going, and {remedy.tail}."
    )
    propagate(world, narrate=True)
    world.say(
        f"At last, the {trial.noun} was no longer wide and dark. The village could cross again, and {hero_name} stood where the break had been, brave and still."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    trial = _safe_fact(world, f, "trial")
    return [
        f'Write a short myth for a child about a brave hero and a {trial.keyword} in the road.',
        f"Tell a gentle old-time story where {hero.label} faces a {trial.noun} and learns bravery while fixing it.",
        f'Write a mythic story that includes the word "{trial.keyword}" and ends with a safe path restored.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    trial = _safe_fact(world, f, "trial")
    remedy = _safe_fact(world, f, "remedy_cfg")
    qa = [
        QAItem(
            question=f"What was broken in the story?",
            answer=f"The {trial.noun} was broken. It split the path and made the crossing unsafe.",
        ),
        QAItem(
            question=f"Why did {hero.label} need bravery?",
            answer=f"{hero.label} needed bravery because the {trial.noun} was dangerous, but {hero.label} still chose to cross and help repair it.",
        ),
        QAItem(
            question=f"What helped {hero.label} repair the rupture?",
            answer=f"{remedy.phrase} helped {hero.label} repair the rupture. The remedy matched the danger and made the path safe again.",
        ),
    ]
    if f["rift"].meters.get("width", 0.0) <= 1.0:
        qa.append(
            QAItem(
                question=f"What changed by the end of the story?",
                answer=f"By the end, the {trial.noun} was narrowed and the village could cross again. {hero.label} had become known for quiet bravery.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing what must be done even when you feel fear. It does not mean fear is gone; it means fear does not win.",
        ),
        QAItem(
            question="What is a rupture?",
            answer="A rupture is a break or split in something that was once whole, like a road, a wall, or the ground.",
        ),
        QAItem(
            question="Why do people build bridges?",
            answer="People build bridges so they can cross water, gaps, or other places that are hard to pass through safely.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    if world.trace:
        lines.append("  trace:")
        lines.extend(f"    - {t}" for t in world.trace)
    return "\n".join(lines)


CURATED = [
    StoryParams("bridge", "chasm", "rope", "Ari", "boy", "steady"),
    StoryParams("cliff", "chasm", "rope", "Mira", "girl", "curious"),
    StoryParams("bridge", "rift", "stones", "Sela", "girl", "quiet"),
]


ASP_RULES = r"""
% A rupture is dangerous when it is a gap in the path.
dangerous(R) :- rupture(R), width(R, W), W > 1.

% A remedy is compatible when it guards the danger and can be carried by the hero.
compatible(RM, R) :- remedy(RM), danger_of(RM, D), danger(R, D).

% A story is valid when the setting allows repair, the rupture is dangerous,
% and some compatible remedy exists for that rupture.
valid_story(S, T, RM) :- setting(S), trial(T), remedy(RM),
    allows_repair(S), rupture_of(T, R), dangerous(R), compatible(RM, R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s_name, s in SETTINGS.items():
        lines.append(asp.fact("setting", s_name))
        if s.sanctum:
            lines.append(asp.fact("sanctum", s_name))
        if "repair" in s.affords:
            lines.append(asp.fact("allows_repair", s_name))
    for t_name, t in TRIALS.items():
        lines.append(asp.fact("trial", t_name))
        lines.append(asp.fact("rupture_of", t_name, t.id))
        lines.append(asp.fact("danger", t.id, t.danger))
        lines.append(asp.fact("width", t.id, 2))
    for r_name, r in REMEDIES.items():
        lines.append(asp.fact("remedy", r_name))
        lines.append(asp.fact("danger_of", r_name, next(iter(r.guards))))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_story_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s, t, r in valid_combos():
        combos.append((s, t, r))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_story_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_story_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld: rupture and bravery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trial", choices=TRIALS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=ADJECTIVES)
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
    combos = valid_combos()
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "trial", None):
        combos = [c for c in combos if c[1] == getattr(args, "trial", None)]
    if getattr(args, "remedy", None):
        combos = [c for c in combos if c[2] == getattr(args, "remedy", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, trial, remedy = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice([n for n, g in HEROES if g == gender])
    trait = getattr(args, "trait", None) or rng.choice(ADJECTIVES)
    return StoryParams(setting, trial, remedy, name, gender, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(TRIALS, params.trial),
        _safe_lookup(REMEDIES, params.remedy),
        params.name,
        params.gender,
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
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible story combos:")
        for row in combos:
            print(" ", row)
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
            header = f"### {p.name}: {p.trial} in {p.setting} (remedy: {p.remedy})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
