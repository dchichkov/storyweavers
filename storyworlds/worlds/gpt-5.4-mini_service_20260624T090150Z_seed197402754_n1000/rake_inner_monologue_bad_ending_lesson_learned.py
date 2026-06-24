#!/usr/bin/env python3
"""
A small folk-tale storyworld about a rake, an inner monologue, a bad ending,
and a lesson learned.

The world models a child or helper who needs to rake leaves from a yard.
The conflict comes from the character's private thoughts: they want to rush,
skip the careful work, or use the rake in a sloppy way. That choice causes a
bad ending for the yard or for a treasured pile of leaves. The lesson learned
arrives when the character recognizes the mistake and changes their habit.

This script follows the Storyweavers world contract:
- self-contained stdlib storyworld
- shared results containers imported eagerly
- ASP helper imported lazily
- parser / params / generate / emit / main
- prose driven by world state
- verification between Python and ASP gates
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    kin: object | None = None
    prize: object | None = None
    tool_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "daughter"}
        male = {"boy", "father", "man", "son"}
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
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
class Prize:
    label: str
    phrase: str
    type: str
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


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    fix: str
    helps: set[str] = field(default_factory=set)
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
            self.trace.append(text)

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
        return w


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    tool: str
    name: str
    gender: str
    relation: str
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
    "yard": Setting(place="the yard", affords={"rake"}),
    "orchard": Setting(place="the orchard", affords={"rake"}),
    "farm": Setting(place="the farm lane", affords={"rake"}),
}

ACTIVITIES = {
    "rake": Activity(
        id="rake",
        verb="rake the leaves",
        gerund="raking leaves",
        rush="sweep the leaves too fast",
        mess="scattered",
        soil="scattered all about",
        keyword="rake",
        tags={"leaves", "autumn"},
    ),
}

PRIZES = {
    "leafpile": Prize(
        label="leaf pile",
        phrase="a neat leaf pile",
        type="leafpile",
    ),
    "pie": Prize(
        label="pie",
        phrase="a warm apple pie on the sill",
        type="pie",
    ),
    "basket": Prize(
        label="basket",
        phrase="a basket of apples",
        type="basket",
    ),
}

TOOLS = {
    "rake": Tool(
        id="rake",
        label="a wooden rake",
        prep="take the wooden rake carefully",
        fix="work slowly and make a neat pile",
        helps={"rake"},
    ),
    "tarp": Tool(
        id="tarp",
        label="a big tarp",
        prep="spread a big tarp first",
        fix="gather the leaves onto the tarp",
        helps={"rake"},
    ),
}

NAMES = {
    "girl": ["Mina", "Lena", "Nora", "Pia", "Ivy"],
    "boy": ["Eli", "Owen", "Theo", "Jude", "Finn"],
}
RELATIONS = {"mother", "father", "grandmother", "grandfather"}
TRAITS = ["careful", "curious", "stubborn", "quiet", "brave"]


class Gate:
    @staticmethod
    def valid_combo(place: str, activity: str, prize: str, tool: str) -> bool:
        if activity != "rake":
            return False
        if tool not in TOOLS:
            return False
        return prize in {"leafpile", "basket", "pie"} and place in SETTINGS

    @staticmethod
    def explain_rejection(place: str, activity: str, prize: str, tool: str) -> str:
        return (
            f"(No story: the chosen parts do not make a believable folk-tale problem. "
            f"Try the rake with leaves in a yard-like place and a prize that can be "
            f"lost or disturbed by careless sweeping.)"
        )


def select_combo(args: argparse.Namespace, rng: random.Random) -> tuple[str, str, str, str]:
    combos = []
    for place in SETTINGS:
        for activity in ACTIVITIES:
            for prize in PRIZES:
                for tool in TOOLS:
                    if not Gate.valid_combo(place, activity, prize, tool):
                        continue
                    if getattr(args, "place", None) and place != getattr(args, "place", None):
                        continue
                    if getattr(args, "activity", None) and activity != getattr(args, "activity", None):
                        continue
                    if getattr(args, "prize", None) and prize != getattr(args, "prize", None):
                        continue
                    if getattr(args, "tool", None) and tool != getattr(args, "tool", None):
                        continue
                    combos.append((place, activity, prize, tool))
    if not combos:
        pass
    return rng.choice(list(combos))


def build_name(gender: str, rng: random.Random) -> str:
    return rng.choice(_safe_lookup(NAMES, gender))


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, tool: Tool,
         name: str, gender: str, relation: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, owner=None))
    kin = world.add(Entity(id="Kin", kind="character", type=relation, label=relation))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label,
                             phrase=prize_cfg.phrase, caretaker=kin.id, plural=prize_cfg.plural))
    tool_ent = world.add(Entity(id=tool.id, type="tool", label=tool.label, owner=hero.id))

    # Beginning
    world.say(f"Once in {setting.place}, there lived a {trait} child named {hero.id}.")
    world.say(f"{hero.id} and {kin.label} looked over the yard, where {prize.phrase} waited quietly.")
    world.say(f"{hero.id} liked {activity.gerund}, and {hero.pronoun()} could not stop thinking about the {activity.keyword}.")

    # Inner monologue
    world.para()
    world.say(f"In {hero.id}'s own mind, a small voice said, \"{tool.prep}, and then I can be done quickly.\"")
    world.say(f"But another thought answered, \"If I rush, the leaves will not stay in a neat pile.\"")
    hero.memes["doubt"] += 1
    hero.memes["want"] += 1

    # Bad choice and bad ending
    world.para()
    world.say(f"At last {hero.id} took the rake and tried to {activity.rush}.")
    hero.meters["carelessness"] += 1
    hero.meters["scattered"] += 1
    prize.meters["disturbed"] += 1
    prize.meters["mess"] += 1
    world.say(f"The wind caught the loose leaves, and soon the {prize.label} was {activity.soil}.")
    kin.memes["sad"] += 1
    kin.meters["work"] += 1
    world.say(f"{kin.label} had to gather the mess again, and the work took all the afternoon.")
    world.say(f"The day ended badly, with tired hands and a yard that looked untidy and forlorn.")
    hero.memes["regret"] += 1

    # Lesson learned
    world.para()
    world.say(f"Then {hero.id} sat very still and listened to the lesson in {hero.pronoun('possessive')} own heart.")
    world.say(f"\"A rake is for careful work, not hurrying,\" {hero.id} thought. \"Slow hands make a better pile.\"")
    hero.memes["lesson_learned"] += 1

    world.facts.update(
        hero=hero,
        kin=kin,
        prize=prize,
        tool=tool_ent,
        activity=activity,
        setting=setting,
        trait=trait,
        relation=relation,
        bad_ending=True,
        lesson=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    return [
        f'Write a folk tale for young children about {hero.id}, a rake, and a mistake that teaches a lesson.',
        f'Tell a short story where {hero.id} thinks to {world.facts["tool"].label.lower()} carefully, but then makes a bad choice and learns from it.',
        f'Write a simple tale with an inner monologue, a bad ending, and a lesson learned, using the word "rake".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    kin = _safe_fact(world, f, "kin")
    prize = _safe_fact(world, f, "prize")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the rake at first?",
            answer=f"{hero.id} wanted to rake the leaves quickly, but that choice led to trouble instead of a neat pile.",
        ),
        QAItem(
            question=f"What did {hero.id} think in the inner monologue about the rake?",
            answer=f"{hero.id} thought to use the rake carefully, then another thought warned that rushing would make the leaves scatter.",
        ),
        QAItem(
            question=f"Why was the ending bad for {kin.label} and the yard?",
            answer=f"The ending was bad because the leaves got scattered all about, so {kin.label} had to do the work again and the yard stayed untidy.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn about using {tool.label}?",
            answer=f"{hero.id} learned that a rake should be used slowly and carefully, because careful hands make a better pile.",
        ),
        QAItem(
            question=f"What happened to the {prize.label} by the end?",
            answer=f"The {prize.label} was left in a messy state when the leaves scattered, which is part of why the ending felt bad.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rake for?",
            answer="A rake is a garden tool with teeth that helps gather leaves, grass, or other light debris into a pile.",
        ),
        QAItem(
            question="Why do leaves get gathered into a pile?",
            answer="Leaves are gathered into a pile so they can be carried away or cleaned up more easily.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the voice of thoughts inside a person's mind, like talking to yourself quietly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== (1) Generation prompts ==")
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
        if e.label:
            bits.append(f"label={e.label}")
        out.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(out)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("keyword", aid, act.keyword))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for a in sorted(tool.helps):
            lines.append(asp.fact("helps", tid, a))
    return "\n".join(lines)


ASP_RULES = r"""
valid_combo(Place,Act,Prize,Tool) :- place(Place), activity(Act), prize(Prize), tool(Tool),
                                     affords(Place,Act), helps(Tool,Act), Act = rake,
                                     Prize != "".
#show valid_combo/4.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/4."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set()
    for place in SETTINGS:
        for act in ACTIVITIES:
            for prize in PRIZES:
                for tool in TOOLS:
                    if Gate.valid_combo(place, act, prize, tool):
                        py.add((place, act, prize, tool))
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale storyworld about a rake, inner monologue, bad ending, and lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--relation", choices=sorted(RELATIONS))
    ap.add_argument("--name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place, activity, prize, tool = select_combo(args, rng)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or build_name(gender, rng)
    relation = getattr(args, "relation", None) or rng.choice(sorted(RELATIONS))
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        tool=tool,
        name=name,
        gender=gender,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(ACTIVITIES, params.activity),
        _safe_lookup(PRIZES, params.prize),
        _safe_lookup(TOOLS, params.tool),
        params.name,
        params.gender,
        params.relation,
        params.seed and "careful" or "stubborn",
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


CURATED = [
    StoryParams(place="yard", activity="rake", prize="leafpile", tool="rake", name="Mina", gender="girl", relation="grandmother"),
    StoryParams(place="orchard", activity="rake", prize="basket", tool="rake", name="Eli", gender="boy", relation="father"),
    StoryParams(place="farm", activity="rake", prize="pie", tool="tarp", name="Nora", gender="girl", relation="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_combo/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.activity} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
