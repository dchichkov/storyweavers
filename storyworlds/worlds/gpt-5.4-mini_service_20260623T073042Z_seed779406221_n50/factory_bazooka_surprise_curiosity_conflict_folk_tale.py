#!/usr/bin/env python3
"""
storyworlds/worlds/factory_bazooka_surprise_curiosity_conflict_folk_tale.py
============================================================================

A small standalone story world in a folk-tale style about a factory, a bazooka,
surprise, curiosity, and conflict. The domain is intentionally tiny: one child,
one elder, one unusual tool, one noisy surprise, and one cautious resolution.

The world is driven by typed entities with physical meters and emotional memes.
It includes a Python reasonableness gate and an inline ASP twin for parity
checks, plus the standard Storyweavers CLI surface.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
FACTORY_NOISE_LIMIT = 1.0



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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    child: object | None = None
    elder: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "maiden"}
        male = {"boy", "man", "father", "smith"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def display(self) -> str:
        return self.label or self.id
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
class Setting:
    place: str
    affirms: set[str] = field(default_factory=set)
    folk_detail: str = ""
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


@dataclass
class Tool:
    id: str
    label: str
    purpose: str
    noise: str
    surprise: str
    mess: str
    power: int
    safe_use: str
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
class Event:
    id: str
    label: str
    cause: str
    effect: str
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
        clone.facts = dict(self.facts)
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


def _r_noise(world: World) -> list[str]:
    out = []
    t = world.entities.get("tool")
    if not t:
        return out
    if t.meters.get("noise", 0.0) < THRESHOLD:
        return out
    if ("noise",) in world.fired:
        return out
    world.fired.add(("noise",))
    child = world.get("child")
    child.memes["surprise"] = child.memes.get("surprise", 0.0) + 1
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1
    out.append("The factory woke with a bang, and the child's eyes went wide.")
    return out


def _r_conflict(world: World) -> list[str]:
    out = []
    child = world.get("child")
    elder = world.get("elder")
    if child.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    if elder.memes.get("warning", 0.0) < THRESHOLD:
        return out
    key = ("conflict",)
    if key in world.fired:
        return out
    world.fired.add(key)
    child.memes["conflict"] = child.memes.get("conflict", 0.0) + 1
    out.append("Curiosity tugged at the child, but the elder's warning made a hard knot of conflict.")
    return out


def _r_settle(world: World) -> list[str]:
    out = []
    child = world.get("child")
    elder = world.get("elder")
    if child.memes.get("conflict", 0.0) < THRESHOLD:
        return out
    if elder.memes.get("guidance", 0.0) < THRESHOLD:
        return out
    key = ("settle",)
    if key in world.fired:
        return out
    world.fired.add(key)
    child.memes["conflict"] = 0.0
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    out.append("The elder showed a safer way, and the knot of conflict came loose.")
    return out


CAUSAL_RULES = [
    Rule("noise", "physical", _r_noise),
    Rule("conflict", "social", _r_conflict),
    Rule("settle", "social", _r_settle),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def valid_combo(setting: str, tool: str, event: str) -> bool:
    return setting in SETTINGS and tool in TOOLS and event in EVENTS


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, t, e) for s in SETTINGS for t in TOOLS for e in EVENTS if valid_combo(s, t, e)]


@dataclass
class StoryParams:
    setting: str
    tool: str
    event: str
    child_name: str
    child_gender: str
    elder_name: str
    elder_gender: str
    seed: Optional[int] = None
    samples: list = field(default_factory=list)
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
    "factory": Setting(
        place="the old factory",
        affirms={"factory"},
        folk_detail="The old factory stood like a sleeping iron giant at the edge of the town.",
    ),
}

TOOLS = {
    "bazooka": Tool(
        id="bazooka",
        label="bazooka",
        purpose="to blast loose dust from the high beams",
        noise="a great boom",
        surprise="like thunder in a tin cup",
        mess="scattered soot",
        power=2,
        safe_use="to clear the dust from the rafters",
        tags={"bazooka"},
    ),
}

EVENTS = {
    "surprise": Event(
        id="surprise",
        label="surprise",
        cause="the bazooka boomed",
        effect="everyone looked up at once",
        tags={"surprise"},
    ),
    "curiosity": Event(
        id="curiosity",
        label="curiosity",
        cause="the child wondered what it was for",
        effect="the child stepped closer",
        tags={"curiosity"},
    ),
    "conflict": Event(
        id="conflict",
        label="conflict",
        cause="the elder warned the child back",
        effect="the child wanted to look anyway",
        tags={"conflict"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Sora", "Nia", "Tia", "Anya"]
BOY_NAMES = ["Ravi", "Bram", "Oren", "Timo", "Leif", "Noah"]
TRAITS = ["curious", "bright-eyed", "soft-hearted", "stubborn"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale factory story with a bazooka, surprise, curiosity, and conflict.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
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
    if getattr(args, "tool", None) and getattr(args, "tool", None) not in TOOLS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "setting", None) and getattr(args, "setting", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "event", None) and getattr(args, "event", None) not in EVENTS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "tool", None) is None or c[1] == getattr(args, "tool", None))
              and (getattr(args, "event", None) is None or c[2] == getattr(args, "event", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, tool, event = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = getattr(args, "elder", None) or rng.choice(["grandmother", "grandfather"])
    elder_name = "Gran" if elder == "grandmother" else "Old Ben"
    return StoryParams(setting, tool, event, name, gender, elder_name, "adult")


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name, traits=["little", "curious"]))
    elder = world.add(Entity(id="elder", kind="character", type="woman", label=params.elder_name, role="elder"))
    tool = world.add(Entity(id="tool", kind="thing", type="thing", label=_safe_lookup(TOOLS, params.tool).label))
    for e in (child, elder, tool):
        e.meters.setdefault("noise", 0.0)
        e.meters.setdefault("dust", 0.0)
        e.memes.setdefault("surprise", 0.0)
        e.memes.setdefault("curiosity", 0.0)
        e.memes.setdefault("conflict", 0.0)
        e.memes.setdefault("joy", 0.0)
    world.say(f"{params.child_name} came to the old factory where the iron rafters slept in shadow.")
    world.say(world.setting.folk_detail)
    world.para()
    world.say(f"Inside, there was a bazooka that was really a big dusty tool, kept {_safe_lookup(TOOLS, params.tool).purpose}.")
    child.memes["curiosity"] += 1
    world.say(f"{params.child_name} felt {_safe_lookup(TOOLS, params.tool).surprise} and wanted to look closer.")
    elder.memes["warning"] += 1
    elder.memes["guidance"] += 1
    world.para()
    tool.meters["noise"] += 1
    tool.meters["dust"] += 1
    propagate(world, narrate=True)
    world.say(f"{params.elder_name} said the bazooka was for grown hands and careful work, not a child's game.")
    child.memes["conflict"] += 1
    world.say(f"{params.child_name} wanted to touch it and also wanted to obey, so {params.child_name} stood in conflict.")
    world.para()
    child.memes["joy"] += 1
    child.memes["conflict"] = 0.0
    world.say(f"Then {params.elder_name} showed how to use a broom for the dust, and the child laughed at the safer trick.")
    world.say(f"By dusk, the factory was tidy, the bazooka was at rest, and the child had learned that a loud surprise can hide a gentle lesson.")
    world.facts.update(child=child, elder=elder, tool=tool, params=params, setting=_safe_lookup(SETTINGS, params.setting))
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a folk tale for a small child about a factory and a bazooka that begins with surprise and ends with a safer choice.',
        f"Tell a child-facing story where {p.child_name} feels curiosity in an old factory, then meets conflict when a bazooka seems tempting.",
        f'Write a simple story that uses the words "factory", "bazooka", "surprise", "curiosity", and "conflict".',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            question=f"Where did {p.child_name} go in the story?",
            answer=f"{p.child_name} went to the old factory, where the rafters were dark and the air felt dusty.",
        ),
        QAItem(
            question=f"What made {p.child_name} curious?",
            answer=f"The bazooka made {p.child_name} curious because it was loud, strange, and meant for careful work.",
        ),
        QAItem(
            question=f"What did the elder do when conflict grew?",
            answer=f"The elder warned {p.child_name} back and then showed a safer way to clean the dust.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a factory?", answer="A factory is a place where things are made or worked on with tools and machines."),
        QAItem(question="What is curiosity?", answer="Curiosity is the wish to know more about something new or strange."),
        QAItem(question="What is conflict?", answer="Conflict is when someone wants two different things at once, and they feel pulled both ways."),
        QAItem(question="What is a surprise?", answer="A surprise is something unexpected that makes people look up or gasp."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: meters={dict(e.meters)} memes={dict(e.memes)} label={e.display}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,T,E) :- setting(S), tool(T), event(E).
has_surprise(T) :- tool(T).
has_curiosity(E) :- event(E), E = curiosity.
has_conflict(E) :- event(E), E = conflict.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
        lines.append(asp.fact("has_surprise", t))
    for e in EVENTS:
        lines.append(asp.fact("event", e))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in ASP:", sorted(cl - py))
    print("only in Python:", sorted(py - cl))
    return 1


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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible combos:\n")
        for s, t, e in asp_valid_combos():
            print(f"  {s:8} {t:8} {e}")
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(StoryParams("factory", "bazooka", e, "Mira", "girl", "Gran")) for e in EVENTS]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
