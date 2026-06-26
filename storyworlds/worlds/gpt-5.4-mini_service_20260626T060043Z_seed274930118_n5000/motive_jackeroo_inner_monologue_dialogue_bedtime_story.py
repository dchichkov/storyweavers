#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/motive_jackeroo_inner_monologue_dialogue_bedtime_story.py
===============================================================================================================

A small bedtime-story world with a child, a jackeroo, a gentle motive to sleep,
and two narrative instruments: inner monologue and dialogue.

Seed words:
- motive
- jackeroo

The story premise:
- A child wants one more moment awake with a cherished jackeroo toy.
- A caregiver offers a bedtime motive: a happier morning if the child rests now.
- The child's inner monologue shifts from resistance to trust.
- Dialogue carries the turn, and the ending proves the change in the room.

This script is a standalone storyworld for the Storyweavers repo.
"""

from __future__ import annotations

import argparse
import copy
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    adult: object | None = None
    blanket: object | None = None
    child: object | None = None
    lamp: object | None = None
    toy: object | None = None
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
    place: str = "the nursery"
    cozy: bool = True
    light_kind: str = "night-light"
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
class Motive:
    id: str
    prompt: str
    benefit: str
    bedtime_effect: str
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
class Jackeroo:
    id: str
    label: str = "jackeroo"
    phrase: str = "a small plush jackeroo with a stitched smile"
    comfort: str = "soft ears"
    bedtime_role: str = "keeper of quiet"
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
    motive: str
    jackeroo: str
    name: str
    gender: str
    caretaker: str
    seed: Optional[int] = None
    params: object | None = None
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
        self.fired: set[tuple] = set()

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
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


def is_reasonable(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.motive in MOTIVES and params.jackeroo in JACKEROOS


def explain_invalid(params: StoryParams) -> str:
    return "(No story: the requested bedtime pieces do not fit this little world.)"


def _r_comfort(world: World) -> list[str]:
    out = []
    child = world.get("child")
    toy = world.get("toy")
    if child.memes.get("fear", 0.0) >= THRESHOLD and toy.held_by == child.id:
        sig = ("comfort",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        child.memes["comfort"] = child.memes.get("comfort", 0.0) + 1.0
        child.memes["fear"] = max(0.0, child.memes.get("fear", 0.0) - 1.0)
        out.append("The little jackeroo felt like a soft answer in the dark.")
    return out


def _r_sleepiness(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.memes.get("calm", 0.0) >= THRESHOLD and child.meters.get("blanket_on", 0.0) >= THRESHOLD:
        sig = ("sleep",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        child.memes["sleepy"] = child.memes.get("sleepy", 0.0) + 1.0
        out.append("Sleepiness tiptoed in like a quiet mouse.")
    return out


RULES = [_r_comfort, _r_sleepiness]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            s = rule(world)
            if s:
                changed = True
                produced.extend(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_sleep(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.memes["fear"] = 1.0
    sim.get("toy").held_by = "child"
    child.meters["blanket_on"] = 1.0
    child.memes["calm"] = 1.0
    propagate(sim, narrate=False)
    return {"sleepy": sim.get("child").memes.get("sleepy", 0.0) >= THRESHOLD}


def tell(setting: Setting, motive: Motive, jackeroo: Jackeroo,
         name: str = "Nora", gender: str = "girl", caretaker: str = "mother") -> World:
    world = World(setting)

    child = world.add(Entity(id="child", kind="character", type=gender, label=name))
    adult = world.add(Entity(id="adult", kind="character", type=caretaker, label=f"the {caretaker}"))
    toy = world.add(Entity(id="toy", type="toy", label=jackeroo.label, phrase=jackeroo.phrase))
    lamp = world.add(Entity(id="lamp", type="thing", label=setting.light_kind))
    lamp.meters["on"] = 1.0
    blanket = world.add(Entity(id="blanket", type="thing", label="blanket"))
    blanket.held_by = child.id

    world.facts.update(child=child, adult=adult, toy=toy, lamp=lamp, blanket=blanket,
                       motive=motive, jackeroo=jackeroo, setting=setting)

    child.memes["awake"] = 1.0
    child.memes["want_more"] = 1.0

    world.say(
        f"{child.label} was a little {gender} who liked the hush of {setting.place} at night."
    )
    world.say(
        f"Beside {child.pronoun('object')} sat {jackeroo.phrase}, and {child.label} called it {jackeroo.label}."
    )
    world.say(
        f"Before bedtime, {child.label} kept one small motive in {child.pronoun('possessive')} mind: {motive.prompt}."
    )

    world.para()
    world.say(
        f"When the room grew dim, {child.label} hugged {toy.label} and thought, "
        f'"Maybe I can stay awake forever if I keep very still."'
    )
    child.memes["fear"] += 1.0
    child.memes["defiance"] += 1.0

    world.say(
        f"Then the {caretaker} looked in and said, "
        f'"If you rest now, {motive.benefit}."'
    )
    child.memes["hope"] = child.memes.get("hope", 0.0) + 1.0

    world.say(
        f"Inside {child.label}'s head, a tiny voice answered, "
        f'"I do not want the day to end, but maybe the morning will feel nicer if I sleep."'
    )

    world.para()
    world.say(
        f"{child.label} whispered, 'Will {jackeroo.label} stay with me?'"
    )
    world.say(
        f'The {caretaker} smiled and said, "Of course. {jackeroo.label} can guard the quiet while you rest."'
    )

    child.memes["fear"] = max(0.0, child.memes.get("fear", 0.0) - 1.0)
    child.memes["calm"] += 1.0
    toy.held_by = child.id
    blanket.held_by = child.id
    child.meters["blanket_on"] = 1.0
    world.say(
        f"{child.label} tucked {jackeroo.label} under {child.pronoun('possessive')} chin and listened to the soft room."
    )
    propagate(world, narrate=True)

    world.para()
    child.memes["sleepy"] = child.memes.get("sleepy", 0.0) + 1.0
    world.say(
        f"{child.label} closed {child.pronoun('possessive')} eyes and let the motive settle at last."
    )
    world.say(
        f"By the end, the lamp was warm, the blanket was snug, and {jackeroo.label} was keeping watch while {child.label} drifted into sleep."
    )

    world.facts["resolved"] = True
    return world


SETTINGS = {
    "nursery": Setting(place="the nursery", cozy=True, light_kind="night-light"),
    "bedroom": Setting(place="the bedroom", cozy=True, light_kind="little lamp"),
    "attic_room": Setting(place="the attic room", cozy=True, light_kind="moon-glow"),
}

MOTIVES = {
    "morning_walk": Motive(
        id="morning_walk",
        prompt="I want to be strong enough for a morning walk",
        benefit="you'll have more energy for the morning walk",
        bedtime_effect="rest brings back springy legs",
    ),
    "storybook": Motive(
        id="storybook",
        prompt="I want to wake up ready for tomorrow's storybook",
        benefit="the next story will feel extra bright after a good sleep",
        bedtime_effect="sleep makes tomorrow's pages easier to enjoy",
    ),
    "sunrise_game": Motive(
        id="sunrise_game",
        prompt="I want to wake up ready for the sunrise game",
        benefit="the sunrise game will be more fun when you feel rested",
        bedtime_effect="rest makes early games feel joyful",
    ),
}

JACKEROOS = {
    "jackeroo": Jackeroo(
        id="jackeroo",
        label="jackeroo",
        phrase="a small plush jackeroo with a stitched smile",
        comfort="soft ears",
        bedtime_role="keeper of quiet",
    ),
    "mama_jackeroo": Jackeroo(
        id="mama_jackeroo",
        label="jackeroo",
        phrase="a bigger plush jackeroo with velvety paws",
        comfort="velvety paws",
        bedtime_role="keeper of quiet",
    ),
}

NAMES = {
    "girl": ["Nora", "Mina", "Lily", "Ada", "June"],
    "boy": ["Finn", "Theo", "Milo", "Eli", "Noah"],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    motive = _safe_fact(world, f, "motive")
    return [
        f'Write a bedtime story for a small child named {child.label} that includes the word "motive".',
        f'Write a gentle story where {child.label} talks with a {f["adult"].type}, a jackeroo, and a sleepy room.',
        f'Write a cozy story with inner monologue and dialogue about why {child.label} chooses to sleep.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    adult = _safe_fact(world, f, "adult")
    motive = _safe_fact(world, f, "motive")
    toy = _safe_fact(world, f, "jackeroo")
    qa = [
        QAItem(
            question=f"What did {child.label} want at first, before the {adult.type} spoke kindly?",
            answer=f"At first, {child.label} wanted to stay awake a little longer with {toy.label}.",
        ),
        QAItem(
            question=f"What was the bedtime motive in the story?",
            answer=f"The motive was {motive.prompt}. That made sleep sound worth choosing.",
        ),
        QAItem(
            question=f"What did the {adult.type} promise about {toy.label}?",
            answer=f"The {adult.type} promised that {toy.label} could stay and guard the quiet while {child.label} slept.",
        ),
        QAItem(
            question=f"How did {child.label} feel at the end?",
            answer=f"{child.label} felt calm and sleepy, then drifted off with {toy.label} close by.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bedtime story?",
            answer="A bedtime story is a gentle story told at night to help a child feel safe, calm, and ready for sleep.",
        ),
        QAItem(
            question="Why do children keep a favorite toy nearby at bedtime?",
            answer="Children often keep a favorite toy nearby because it feels familiar and comforting in the dark.",
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is the quiet talking a character does inside their own head.",
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is the spoken conversation between characters.",
        ),
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
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
% A bedtime story is valid when the motive, jackeroo, and cozy setting are all present.
valid_story(S, M, J) :- setting(S), motive(M), jackeroo(J), cozy(S).

% The child becomes sleepy when comfort and calm are both present.
sleepy(child) :- calm(child), comfort(child).

% The ending is reasonable when the toy is close, the blanket is on, and sleepiness arrives.
happy_end(S, M, J) :- valid_story(S, M, J), sleepy(child), held(toy, child), blanket_on(child).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.cozy:
            lines.append(asp.fact("cozy", sid))
    for mid, m in MOTIVES.items():
        lines.append(asp.fact("motive", mid))
    for jid, j in JACKEROOS.items():
        lines.append(asp.fact("jackeroo", jid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(s, m, j) for s in SETTINGS for m in MOTIVES for j in JACKEROOS}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cozy bedtime story world with a jackeroo and a motive.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--motive", choices=MOTIVES)
    ap.add_argument("--jackeroo", choices=JACKEROOS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caretaker", choices=["mother", "father"])
    ap.add_argument("--name")
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
    motive = getattr(args, "motive", None) or rng.choice(list(MOTIVES))
    jackeroo = getattr(args, "jackeroo", None) or rng.choice(list(JACKEROOS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    caretaker = getattr(args, "caretaker", None) or rng.choice(["mother", "father"])
    params = StoryParams(setting=setting, motive=motive, jackeroo=jackeroo, name=name, gender=gender, caretaker=caretaker)
    if not is_reasonable(params):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(MOTIVES, params.motive), _safe_lookup(JACKEROOS, params.jackeroo),
                 params.name, params.gender, params.caretaker)
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
        combos = asp.atoms(model, "valid_story")
        print(f"{len(combos)} compatible bedtime combos:")
        for row in combos:
            print("  ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams("nursery", "morning_walk", "jackeroo", "Nora", "girl", "mother"),
            StoryParams("bedroom", "storybook", "mama_jackeroo", "Finn", "boy", "father"),
            StoryParams("attic_room", "sunrise_game", "jackeroo", "Lily", "girl", "mother"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
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
