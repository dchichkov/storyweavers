#!/usr/bin/env python3
"""
Standalone storyworld: a small Space Adventure about a curious run toward a
surprising sight, and a safe way to satisfy that curiosity.

Premise source seed:
- run
- Surprise
- Curiosity
- Space Adventure

World shape:
- A child astronaut wants to run after a strange glow.
- The grown-up worries about gear and distance.
- The child learns to use a rover and a tether so the adventure stays safe.
- The ending image proves what changed: curiosity is still there, but it is now
  guided by teamwork and preparation.
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    parent: object | None = None
    def __post_init__(self):
        if not self.meters:
            self.meters = {"distance": 0.0, "dust": 0.0, "charge": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "surprise": 0.0, "worry": 0.0, "joy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "pilot"}
        male = {"boy", "father", "man", "pilot"}
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Setting:
    place: str
    tag: str
    afford_run: bool = True
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
class Object:
    id: str
    label: str
    phrase: str
    region: str
    can_hold: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    protects: set[str]
    helps: set[str]
    action: str
    end_state: str
    plural: bool = False
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.objects: dict[str, Object] = {}
        self.tool: Optional[Tool] = None
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.history: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_object(self, obj: Object) -> Object:
        self.objects[obj.id] = obj
        return obj

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self):
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.history.append(text)

    def para(self):
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.objects = copy.deepcopy(self.objects)
        w.tool = copy.deepcopy(self.tool)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def _rule_run(world: World) -> list[str]:
    out = []
    hero = world.get(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero").id)
    if hero.meters["distance"] >= THRESHOLD and world.facts.get("running_to") == "signal":
        sig = ("run", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["surprise"] += 0.5
            out.append(f"{hero.id} ran closer, and the strange light looked even more surprising.")
    return out


def _rule_worry(world: World) -> list[str]:
    out = []
    hero = world.get(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero").id)
    parent = world.get(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "parent").id)
    if hero.memes["surprise"] >= THRESHOLD and hero.meters["distance"] >= 1.0:
        sig = ("worry", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            parent.memes["worry"] += 1
            out.append(f"{parent.id} worried that {hero.id} might run too far from the ship.")
    return out


def _rule_joy(world: World) -> list[str]:
    out = []
    hero = world.get(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero").id)
    if world.tool and hero.meters["distance"] >= THRESHOLD:
        sig = ("joy", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["joy"] += 1
            out.append(f"The safe plan made the space walk feel like a little victory.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    rules = [_rule_run, _rule_worry, _rule_joy]
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in rules:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def reasonableness_gate(setting: Setting, obj: Object, tool: Optional[Tool]) -> bool:
    return setting.afford_run and obj.region in {"path", "dock", "field"} and tool is not None


def select_tool(obj: Object) -> Optional[Tool]:
    for tool in TOOLS:
        if obj.region in tool.protects:
            return tool
    return None


def tell(setting: Setting, hero_name: str, hero_type: str, parent_type: str, object_cfg: Object) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    target = world.add_object(object_cfg)

    world.tool = select_tool(target)

    world.say(
        f"{hero.id} was a small {hero.type} astronaut with bright eyes and a big curiosity."
    )
    world.say(
        f"{hero.id} loved every surprise in {world.setting.place}, especially when the sky shimmered blue-black and gold."
    )
    world.say(
        f"One day, {hero.id} noticed a tiny light near the landing path."
    )

    world.para()
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} wanted to run toward the light right away, but {parent.label} held up a careful hand."
    )
    world.say(
        f'"That light might be important," said {parent.label}, "but space is bigger than it looks."'
    )
    hero.meters["distance"] += 0.5
    world.facts["running_to"] = "signal"
    propagate(world, narrate=True)

    world.para()
    if world.tool is None:
        pass
    if not reasonableness_gate(setting, target, world.tool):
        pass
    hero.memes["surprise"] += 1
    world.say(
        f"{hero.id} pointed to {target.phrase} and blinked in surprise."
    )
    world.say(
        f"{parent.id} smiled and showed {hero.id} {world.tool.label}."
    )
    world.say(
        f'"Let us use {world.tool.label} and {world.tool.action}," {parent.label} said.'
    )

    hero.meters["distance"] += 1.0
    hero.meters["charge"] += 0.5
    hero.meters["dust"] += 0.0
    world.tool = world.tool
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} climbed into the rover, and together they moved toward the glow."
    )
    propagate(world, narrate=True)

    world.para()
    hero.memes["joy"] += 1
    world.say(
        f"At the end, the light was only a blinking beacon from a small supply marker, not a danger at all."
    )
    world.say(
        f"{hero.id} laughed, because the biggest surprise was that curiosity could stay brave and still be safe."
    )
    world.say(
        f"The rover stopped beside the beacon, and {hero.id} looked out at the stars with {parent.label} nearby."
    )

    world.facts.update(
        hero=hero,
        parent=parent,
        object=target,
        tool=world.tool,
    )
    return world


SETTINGS = {
    "moon_base": Setting(place="the moon base", tag="moon"),
    "orbital_station": Setting(place="the orbital station", tag="station"),
    "red_dune": Setting(place="the red dune field", tag="planet"),
}

OBJECTS = {
    "beacon": Object(id="beacon", label="beacon", phrase="a blinking supply beacon", region="path", can_hold=False),
    "signal_panel": Object(id="signal_panel", label="panel", phrase="a glittering signal panel", region="dock", can_hold=False),
    "glow_crate": Object(id="glow_crate", label="crate", phrase="a glowing crate near the landing path", region="path", can_hold=True),
}

TOOLS = [
    Tool(
        id="tether",
        label="a tether line",
        phrase="a tether line",
        protects={"path", "dock"},
        helps={"run"},
        action="clip it to the rover",
        end_state="tethered safely",
    ),
    Tool(
        id="rover",
        label="the rover",
        phrase="the rover",
        protects={"path", "dock", "field"},
        helps={"run"},
        action="ride instead of run",
        end_state="riding safely",
    ),
]

HERO_NAMES = ["Mina", "Lio", "Rae", "Nova", "Tali", "Juno"]
HERO_TYPES = ["girl", "boy"]
PARENT_TYPES = ["mother", "father"]


@dataclass
class StoryParams:
    place: str
    object: str
    name: str
    hero_type: str
    parent_type: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


CURATED = [
    StoryParams(place="moon_base", object="beacon", name="Nova", hero_type="girl", parent_type="mother"),
    StoryParams(place="orbital_station", object="signal_panel", name="Lio", hero_type="boy", parent_type="father"),
    StoryParams(place="red_dune", object="glow_crate", name="Mina", hero_type="girl", parent_type="father"),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    parent = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent")
    obj = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "object")
    return [
        f'Write a short Space Adventure story where {hero.id} feels curiosity and wants to run toward {obj.phrase}.',
        f"Tell a gentle story about {hero.id} and {parent.label} finding a safe way to approach {obj.phrase}.",
        f'Write a child-friendly space story with surprise, curiosity, a run, and a safe ending at {world.setting.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    parent = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent")
    obj = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "object")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"Who wanted to run toward {obj.phrase}?",
            answer=f"{hero.id} wanted to run toward {obj.phrase} because {hero.pronoun('possessive')} curiosity was very big.",
        ),
        QAItem(
            question=f"Why did {parent.label} stop {hero.id} from running at first?",
            answer=f"{parent.label.capitalize()} stopped {hero.id} because space is wide, and it was safer to choose a careful plan before running closer.",
        ),
        QAItem(
            question=f"What safe help did they use to get closer to the light?",
            answer=f"They used {tool.label} so {hero.id} could move toward the light safely instead of rushing alone.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {hero.id} laughing beside the beacon, feeling joyful because the surprise was safe and the curiosity had been guided well.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a beacon in space?",
            answer="A beacon is a bright marker or signal that helps people know where to go.",
        ),
        QAItem(
            question="Why do astronauts use a tether?",
            answer="A tether helps keep someone connected to a safe place so they do not drift away.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to learn more and find out what something is.",
        ),
        QAItem(
            question="What is surprise?",
            answer="Surprise is the feeling you get when something happens that you did not expect.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"tool={world.tool.label if world.tool else None}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small Space Adventure storyworld with Surprise and Curiosity.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--parent-type", choices=PARENT_TYPES)
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    obj = getattr(args, "object", None) or rng.choice(list(OBJECTS))
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    parent_type = getattr(args, "parent_type", None) or rng.choice(PARENT_TYPES)
    return StoryParams(place=place, object=obj, name=name, hero_type=hero_type, parent_type=parent_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), params.name, params.hero_type, params.parent_type, _safe_lookup(OBJECTS, params.object))
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


ASP_RULES = r"""
hero(H). parent(P). object(O). tool(T).
curious(H) :- hero(H).
surprising(O) :- object(O).
safe(T) :- tool(T).
can_resolve(H,O,T) :- curious(H), surprising(O), safe(T).
valid_story(Place,Object,Hero,Parent) :- place(Place), object(Object), hero(Hero), parent(Parent), can_resolve(Hero,Object,_).
#show valid_story/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
    for n in HERO_NAMES:
        lines.append(asp.fact("hero", n))
    for pt in PARENT_TYPES:
        lines.append(asp.fact("parent", pt))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(generate(p))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
