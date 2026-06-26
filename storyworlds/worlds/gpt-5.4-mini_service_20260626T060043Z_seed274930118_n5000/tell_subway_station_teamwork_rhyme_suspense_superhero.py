#!/usr/bin/env python3
"""
Superhero storyworld: a subway-station rescue with teamwork, rhyme, and suspense.

A small child-facing simulation with physical meters and emotional memes:
- a hero, a sidekick, a commuter crowd, and a troublemaking menace
- a delayed train, a stuck station gate, and a rescue that requires teamwork
- rhyme in the dialogue, suspense in the buildup, and a triumphant ending image

The story is built from state changes, not a frozen template.
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
# Core entities and simulation
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
    label: str = ""
    type: str = "thing"
    role: str = ""
    plural: bool = False
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    crowd: object | None = None
    hero: object | None = None
    sidekick: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
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
    place: str = "the subway station"
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
class Threat:
    id: str
    label: str
    danger: str
    rhyme: str
    mess: str
    tension_gain: float
    rescue_need: str
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
class Gear:
    id: str
    label: str
    role: str
    helps: set[str]
    action: str
    rhyme: str
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
        self.fired: set[tuple] = set()
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}

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
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)


def meters(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def add_meter(ent: Entity, key: str, value: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + value


def add_meme(ent: Entity, key: str, value: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + value


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "station": Setting(place="the subway station", affords={"stuck_gate", "lost_train", "crowd_crush"}),
}

HEROES = [
    ("Nova", "girl", "heroine"),
    ("Comet", "boy", "hero"),
    ("Pulse", "girl", "heroine"),
    ("Bolt", "boy", "hero"),
]

SIDEKICKS = [
    ("Zip", "girl", "sidekick"),
    ("Dash", "boy", "sidekick"),
    ("Echo", "girl", "sidekick"),
    ("Spark", "boy", "sidekick"),
]

THREATS = {
    "stuck_gate": Threat(
        id="stuck_gate",
        label="a stuck station gate",
        danger="the gate would trap the crowd on the wrong side",
        rhyme="lock and block",
        mess="panic",
        tension_gain=1.0,
        rescue_need="open the gate fast",
    ),
    "lost_train": Threat(
        id="lost_train",
        label="a train that might leave too soon",
        danger="the last train would roll away before everyone got aboard",
        rhyme="sweep and leap",
        mess="worry",
        tension_gain=1.0,
        rescue_need="signal the train in time",
    ),
    "crowd_crush": Threat(
        id="crowd_crush",
        label="a packed platform with no room to breathe",
        danger="people would press together and get scared",
        rhyme="guide and side",
        mess="alarm",
        tension_gain=1.0,
        rescue_need="guide the crowd safely",
    ),
}

GEAR = {
    "bright_lights": Gear(
        id="bright_lights",
        label="bright rescue lights",
        role="helper",
        helps={"stuck_gate", "crowd_crush"},
        action="shone",
        rhyme="light and bright",
    ),
    "rope_line": Gear(
        id="rope_line",
        label="a rope line",
        role="helper",
        helps={"crowd_crush", "lost_train"},
        action="held",
        rhyme="line and shine",
    ),
    "train_whistle": Gear(
        id="train_whistle",
        label="a sharp whistle",
        role="helper",
        helps={"lost_train"},
        action="whistled",
        rhyme="squeal and reveal",
    ),
}

NAMES = ["Ari", "Mila", "Jude", "Tia", "Noah", "Luna", "Max", "Zuri"]
TRAITS = ["brave", "quick", "kind", "clever", "steady"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    threat: str
    name: str
    gender: str
    sidekick: str
    sidekick_gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasoning
# ---------------------------------------------------------------------------
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


def threat_requires_teamwork(threat: Threat) -> bool:
    return True


def select_gear(threat_id: str) -> list[Gear]:
    return [g for g in GEAR.values() if threat_id in g.helps]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for threat_id in THREATS:
        if select_gear(threat_id):
            combos.append(("station", threat_id, "teamwork"))
    return combos


def explain_rejection(threat_id: str) -> str:
    if not select_gear(threat_id):
        return "(No story: this trouble has no helpful gear, so the rescue cannot be solved honestly.)"
    return "(No story: the requested options do not make a valid subway rescue.)"


# ---------------------------------------------------------------------------
# Simulation actions
# ---------------------------------------------------------------------------
def intro(world: World, hero: Entity, sidekick: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.memes.get('trait_word', 'brave')} superhero who watched over {world.setting.place}. "
        f"{sidekick.id} was {hero.pronoun('possessive')} quick sidekick, and together they loved helping people."
    )


def build_suspense(world: World, threat: Threat, crowd: Entity) -> None:
    add_meme(crowd, "worry", 1)
    add_meter(crowd, "pressure", 1)
    world.say(
        f"Down below, {threat.label} made the platform feel tense. "
        f"{threat.danger.capitalize()}, and the station hummed with suspense."
    )


def call_teamwork(world: World, hero: Entity, sidekick: Entity, threat: Threat) -> None:
    add_meme(hero, "resolve", 1)
    add_meme(sidekick, "resolve", 1)
    add_meme(hero, "teamwork", 1)
    add_meme(sidekick, "teamwork", 1)
    world.say(
        f'{hero.id} said, "We can do it, quick and slick." '
        f'{sidekick.id} said, "With two good pals, we save the day in a flash!"'
    )
    world.say(
        f"They moved like a pair, one to watch, one to dash, ready to {threat.rescue_need}."
    )


def use_gear(world: World, threat: Threat, gear: Gear) -> None:
    world.say(
        f"{gear.label.capitalize()} {gear.action} with a glow, and the plan began to show."
    )
    add_meter(world.get("station"), "helped", 1)


def resolve(world: World, hero: Entity, sidekick: Entity, crowd: Entity, threat: Threat, gear: Gear) -> None:
    add_meter(crowd, "safe", 1)
    add_meme(crowd, "relief", 1)
    add_meme(hero, "joy", 1)
    add_meme(sidekick, "joy", 1)
    world.say(
        f"Together they used {gear.label} to {threat.rescue_need}. "
        f"The crowd flowed through, safe and sound, with room again on the ground."
    )
    world.say(
        f"{hero.id} and {sidekick.id} stood by the doors and smiled. "
        f"The station was calm, and the night felt bright."
    )


def tell(threat_id: str, hero_name: str = "Nova", hero_gender: str = "girl",
         sidekick_name: str = "Zip", sidekick_gender: str = "girl",
         trait: str = "brave") -> World:
    world = World(SETTINGS["station"])
    threat = _safe_lookup(THREATS, threat_id)

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type=sidekick_gender, role="sidekick"))
    crowd = world.add(Entity(id="crowd", kind="group", type="crowd", plural=True, role="commuters"))

    hero.memes["trait_word"] = trait
    sidekick.memes["trait_word"] = "quick"

    intro(world, hero, sidekick)
    world.para()
    build_suspense(world, threat, crowd)
    call_teamwork(world, hero, sidekick, threat)

    gear = select_gear(threat_id)[0]
    world.para()
    use_gear(world, threat, gear)
    resolve(world, hero, sidekick, crowd, threat, gear)

    world.facts = {
        "threat": threat,
        "gear": gear,
        "hero": hero,
        "sidekick": sidekick,
        "crowd": crowd,
        "setting": world.setting,
    }
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story set in a subway station that includes teamwork and the word "tell".',
        f"Tell a suspenseful rhyme-filled rescue story where {f['hero'].id} and {f['sidekick'].id} work together to fix {f['threat'].label}.",
        f"Write a child-friendly superhero story about a station problem, a brave team, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    sidekick: Entity = _safe_fact(world, f, "sidekick")
    threat: Threat = _safe_fact(world, f, "threat")
    gear: Gear = _safe_fact(world, f, "gear")
    crowd: Entity = _safe_fact(world, f, "crowd")
    qa = [
        QAItem(
            question=f"Who were the two heroes in the subway station story?",
            answer=f"The heroes were {hero.id} and {sidekick.id}. They worked together to help the people in the station.",
        ),
        QAItem(
            question=f"What trouble made the story suspenseful?",
            answer=f"The trouble was {threat.label}. It made the platform feel tense because {threat.danger}.",
        ),
        QAItem(
            question=f"What helped the heroes fix the problem?",
            answer=f"{gear.label.capitalize()} helped them. It was the tool that let the team {threat.rescue_need}.",
        ),
        QAItem(
            question=f"How did the crowd feel before the rescue?",
            answer=f"The crowd felt worried and packed together, because the station problem made everyone tense.",
        ),
        QAItem(
            question=f"How did the heroes solve the problem in the end?",
            answer=f"They used teamwork, chose {gear.label}, and helped the crowd move safely again.",
        ),
    ]
    if meters(crowd, "safe") > 0:
        qa.append(
            QAItem(
                question="What ending image showed that the rescue was over?",
                answer="The station was calm again, the crowd had room to breathe, and the heroes were smiling by the doors.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a subway station?",
            answer="A subway station is a place where people wait for underground trains and walk through gates to reach the platform.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and use their different skills together to finish a job.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of wondering what will happen next when a problem is getting close.",
        ),
        QAItem(
            question="Why do heroes sometimes speak in rhyme?",
            answer="Rhyming lines can make a story sound playful, memorable, and fun to listen to.",
        ),
    ]


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
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        out.append(f"  {e.id}: {e.kind} {', '.join(bits)}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A valid story is a station rescue with teamwork and a useful gear choice.
valid_story(P, T) :- place(P), threat(T), has_gear(T), teamwork(T).
has_gear(T) :- gear(G), helps(G, T).
teamwork(T) :- teamwork_theme(T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid in THREATS:
        lines.append(asp.fact("threat", tid))
        lines.append(asp.fact("teamwork_theme", tid))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for t in sorted(g.helps):
            lines.append(asp.fact("helps", gid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: ASP matches Python gate ({len(python_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    if python_set - asp_set:
        print("Only in Python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("Only in ASP:", sorted(asp_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    return [("station", tid, "teamwork") for tid in THREATS if select_gear(tid)]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "threat", None) and getattr(args, "threat", None) not in THREATS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    threat_id = getattr(args, "threat", None) or rng.choice(list(THREATS))
    if not select_gear(threat_id):
        return _fallback_storyparams(args, rng, StoryParams, globals())

    hero_name, hero_gender, _ = rng.choice(HEROES)
    sidekick_name, sidekick_gender, _ = rng.choice(SIDEKICKS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    if getattr(args, "name", None):
        hero_name = getattr(args, "name", None)
    if getattr(args, "gender", None):
        hero_gender = getattr(args, "gender", None)
    if getattr(args, "sidekick", None):
        sidekick_name = getattr(args, "sidekick", None)
    if getattr(args, "sidekick_gender", None):
        sidekick_gender = getattr(args, "sidekick_gender", None)

    return StoryParams(
        threat=threat_id,
        name=hero_name,
        gender=hero_gender,
        sidekick=sidekick_name,
        sidekick_gender=sidekick_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params.threat, params.name, params.gender, params.sidekick, params.sidekick_gender, params.trait)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(threat="stuck_gate", name="Nova", gender="girl", sidekick="Zip", sidekick_gender="girl", trait="brave"),
    StoryParams(threat="lost_train", name="Comet", gender="boy", sidekick="Dash", sidekick_gender="boy", trait="clever"),
    StoryParams(threat="crowd_crush", name="Pulse", gender="girl", sidekick="Echo", sidekick_gender="girl", trait="steady"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld set in a subway station with teamwork, rhyme, and suspense.")
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--sidekick")
    ap.add_argument("--sidekick-gender", choices=["girl", "boy"])
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid_story/2."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
