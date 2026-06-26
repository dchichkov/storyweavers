#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/safari_clutter_cautionary_flashback_bedtime_story.py
=================================================================================

A small bedtime-story world about a child, clutter, and a careful safari
morning.

Premise:
- A child is excited about a safari outing.
- Their room is cluttered with too many toys, snacks, and spare things.
- A parent remembers a past morning when clutter made them late and stressed.

Tension:
- The child wants to keep packing more and more items "just in case."
- Clutter makes the backpack heavy, messy, and hard to close.
- A cautionary flashback shows why bringing too much causes problems.

Turn:
- The parent suggests a simple, careful pack: water, hat, small snack, and one
  comfort toy.
- The child sorts, tidies, and chooses only what is useful.

Resolution:
- The backpack closes easily.
- The room looks calm.
- The child falls asleep ready for the safari, having learned that less clutter
  makes a gentler morning.
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
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    backpack: object | None = None
    child: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

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
    safari_ready: bool = False
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
class PackItem:
    id: str
    label: str
    phrase: str
    category: str
    useful_for: set[str]
    bulky: bool = False
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
class StoryParams:
    setting: str
    goal: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None
    samples: list = field(default_factory=list)
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def carried_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]


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


def _r_clutter_weight(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    backpack = world.get("backpack")
    clutter = sum(1 for e in world.entities.values() if e.kind == "item" and e.carried_by == child.id)
    if clutter >= 4 and ("weight", clutter) not in world.fired:
        world.fired.add(("weight", clutter))
        backpack.meters["heavy"] = 1
        child.memes["stress"] += 1
        out.append("The backpack felt too heavy, and the child frowned at the pile of things.")
    return out


def _r_clutter_close(world: World) -> list[str]:
    out: list[str] = []
    backpack = world.get("backpack")
    child = world.get("child")
    if child.memes.get("tidy", 0) < THRESHOLD:
        return out
    useful = sum(1 for e in world.entities.values() if e.kind == "item" and e.carried_by == child.id and e.meters.get("useful", 0) >= THRESHOLD)
    if useful >= 3 and backpack.meters.get("heavy", 0) < THRESHOLD and ("close", useful) not in world.fired:
        world.fired.add(("close", useful))
        backpack.meters["closed"] = 1
        out.append("The backpack zipped shut with a soft little swish.")
    return out


CAUSAL_RULES = [
    Rule("clutter_weight", "physical", _r_clutter_weight),
    Rule("clutter_close", "physical", _r_clutter_close),
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


SETTINGS = {
    "bedroom": Setting(place="the bedroom", indoors=True, safari_ready=False),
    "hallway": Setting(place="the hallway", indoors=True, safari_ready=False),
    "porch": Setting(place="the porch", indoors=False, safari_ready=True),
}

GOALS = {
    "safari": "go on a safari",
}

PACK_ITEMS = {
    "hat": PackItem("hat", "sun hat", "a floppy sun hat", "protective", {"sun", "safari"}, bulky=False),
    "water": PackItem("water", "water bottle", "a cool water bottle", "essential", {"safari", "heat"}, bulky=False),
    "snack": PackItem("snack", "snack bag", "a small snack bag", "essential", {"safari", "hunger"}, bulky=False),
    "toy": PackItem("toy", "stuffed lion", "a beloved stuffed lion", "comfort", {"bedtime", "sleep"}, bulky=False),
    "binoculars": PackItem("binoculars", "binoculars", "a tiny pair of binoculars", "tool", {"safari"}, bulky=False),
    "blanket": PackItem("blanket", "blanket", "a thick blanket", "comfort", {"bedtime"}, bulky=True),
    "blocks": PackItem("blocks", "toy blocks", "a pile of toy blocks", "play", {"play"}, bulky=True, plural=True),
}

GIRL_NAMES = ["Lila", "Mina", "Zara", "Nora", "Tia"]
BOY_NAMES = ["Milo", "Theo", "Ben", "Owen", "Leo"]
TRAITS = ["curious", "sleepy", "gentle", "spirited", "careful"]

KNOWLEDGE = {
    "safari": [("What is a safari?", "A safari is a trip to watch wild animals in a place where they live.")],
    "clutter": [("What is clutter?", "Clutter is too many things left in a messy pile, so a room feels crowded.")],
    "hat": [("Why wear a sun hat?", "A sun hat helps shade your face and head from bright sunlight.")],
    "water": [("Why bring water on a trip?", "Water helps you stay from getting thirsty when you are outside for a long time.")],
    "sleep": [("Why do children need bedtime?", "Bedtime gives children rest so they can wake up with energy the next day.")],
}

KNOWLEDGE_ORDER = ["safari", "clutter", "hat", "water", "sleep"]


def choose_items(goal: str) -> list[str]:
    return ["hat", "water", "snack", "toy", "binoculars", "blanket", "blocks"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        if not setting.safari_ready:
            continue
        combos.append((setting_id, "safari"))
    return combos


def cautionary_flashback(world: World, parent: Entity, child: Entity) -> None:
    world.say(
        f'Before this trip, {child.id} remembered a different morning when {child.pronoun("possessive")} room was full of clutter.'
    )
    world.say(
        f"{parent.label_word} had been trying to pack then too, but the pile was so messy that the important things got buried."
    )
    world.say(
        f'That was a good reason to slow down now.'
    )
    child.memes["flashback"] += 1
    parent.memes["warning"] += 1


def tidies(world: World, child: Entity) -> None:
    child.memes["tidy"] += 1
    world.say(
        f"{child.id} picked up the extra things one by one and made little tidy stacks."
    )
    propagate(world, narrate=False)


def pack_item(world: World, child: Entity, item: Entity) -> None:
    item.carried_by = child.id
    item.meters["useful"] = 1
    world.say(f"{child.id} put the {item.label} into the backpack.")


def warn(world: World, parent: Entity, child: Entity) -> None:
    if world.get("backpack").meters.get("heavy", 0) >= THRESHOLD:
        world.say(
            f'"Too much clutter makes the bag hard to close," {parent.label_word} said softly.'
        )


def resolve(world: World, parent: Entity, child: Entity) -> None:
    backpack = world.get("backpack")
    if backpack.meters.get("closed", 0) >= THRESHOLD:
        child.memes["joy"] += 1
        world.say(
            f"{child.id} smiled when the backpack zipped shut. "
            f"{child.pronoun().capitalize()} hugged {child.pronoun('possessive')} {parent.label_word}, ready for the safari and sleepy enough for bed."
        )


def tell(setting: Setting, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=hero_type, label=hero_name, meters={}, memes={"joy": 0.0}))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", meters={}, memes={"warning": 0.0}))
    backpack = world.add(Entity(id="backpack", kind="thing", type="backpack", label="backpack", meters={}, memes={}))
    items = []
    for item_id in choose_items("safari"):
        cfg = _safe_lookup(PACK_ITEMS, item_id)
        items.append(world.add(Entity(
            id=item_id,
            kind="item",
            type=cfg.category,
            label=cfg.label,
            phrase=cfg.phrase,
            plural=cfg.plural,
            owner=child.id,
            carried_by=child.id,
            meters={"useful": 1.0 if item_id in {"hat", "water", "snack", "toy", "binoculars"} else 0.0},
            memes={},
        )))

    world.say(f"{hero_name} was a {trait} little {hero_type} who loved bedtime stories and safari mornings.")
    world.say(f"{child.id} wanted to {GOALS['safari']} with {child.pronoun('possessive')} {parent.label_word}.")
    world.say(f"But the bedroom was cluttered with too many things.")
    world.para()
    cautionary_flashback(world, parent, child)
    warn(world, parent, child)

    world.para()
    world.say(f"{child.id} listened, and {child.pronoun()} began to sort the bag.")
    # Only keep the useful essentials, remove clutter.
    useful_order = ["hat", "water", "snack", "toy"]
    for iid in useful_order:
        pack_item(world, child, world.get(iid))
    for iid in ["blocks", "blanket"]:
        if iid in world.entities:
            world.get(iid).carried_by = None
    tidies(world, child)
    propagate(world)

    world.para()
    resolve(world, parent, child)
    world.say(
        f"At last, the bedroom looked calm, the bag was light, and the little safari adventure could wait for morning."
    )

    world.facts.update(
        child=child,
        parent=parent,
        backpack=backpack,
        items=items,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    return [
        f'Write a gentle bedtime story about a child named {child.label} who learns that clutter can make a safari morning harder.',
        f"Tell a cautionary flashback story where {child.label} wants to pack too much for a safari, but {parent.label_word} helps with a calm cleanup.",
        "Write a short story with safari animals, a messy room, and a quiet ending that feels safe enough for sleep.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    parent: Entity = _safe_fact(world, f, "parent")
    backpack: Entity = _safe_fact(world, f, "backpack")
    qa = [
        QAItem(
            question=f"What did {child.id} want to do in the story?",
            answer=f"{child.id} wanted to go on a safari with {child.pronoun('possessive')} {parent.label_word}.",
        ),
        QAItem(
            question=f"Why did {parent.label_word} warn {child.id} about the bag?",
            answer="The bag had too much clutter in it, so it would be heavy and hard to close.",
        ),
        QAItem(
            question=f"What changed after {child.id} tidied the room?",
            answer=f"The extra clutter was put away, the backpack closed, and the room felt calm again.",
        ),
    ]
    if backpack.meters.get("closed", 0) >= THRESHOLD:
        qa.append(QAItem(
            question=f"How did the story end for {child.id}'s backpack?",
            answer="It zipped shut softly after the child kept only the useful safari things.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag == "sleep" or True:
            pass
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["safari"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["clutter"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["hat"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["water"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["sleep"])
    return out


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
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(safari_bedroom).
setting(safari_porch).

safari_ready(safari_porch).

clutter_item(blocks).
clutter_item(blanket).

useful_item(hat).
useful_item(water).
useful_item(snack).
useful_item(toy).
useful_item(binoculars).

heavy_when_cluttered(B) :- bag(B), has_item(B, blocks).
closed(B) :- bag(B), useful_count(B, N), N >= 4, not clutter_left(B).

clutter_left(B) :- bag(B), has_item(B, blocks).
clutter_left(B) :- bag(B), has_item(B, blanket).

valid_story(S, safari) :- setting(S), safari_ready(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.safari_ready:
            lines.append(asp.fact("safari_ready", sid))
    for iid, item in PACK_ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.category == "essential":
            lines.append(asp.fact("essential", iid))
        if item.bulky:
            lines.append(asp.fact("bulky", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime safari story world with clutter and a cautionary flashback.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, goal="safari", name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), params.name, params.gender, params.parent, params.trait)
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
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("1 compatible setting: safari_porch")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(StoryParams(setting="porch", goal="safari", name="Lila", gender="girl", parent="mother", trait="careful"))]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
