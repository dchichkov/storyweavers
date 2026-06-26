#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/sleepy_marriage_sound_effects_happy_ending_mystery.py
================================================================================

A small, standalone story world about a sleepy marriage-day mystery with
sound effects and a happy ending.

Premise seed:
- sleepy
- marriage

Story shape:
- A quiet wedding setup
- A puzzling sound-effect mystery
- A careful search and reveal
- A happy ending with the marriage completed

The world is deliberately small and constraint-checked: a few plausible
variants, each driven by world state rather than a fixed paragraph shell.
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    phrases: str = ""
    bride: object | None = None
    detective: object | None = None
    groom: object | None = None
    helper_ent: object | None = None
    item_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"bride", "woman", "girl"}
        male = {"groom", "man", "boy"}
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
    indoor: bool
    echo: bool = False
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
class Clue:
    sound: str
    source: str
    reveal: str
    intensity: str
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
class WeddingItem:
    id: str
    label: str
    phrase: str
    type: str
    importance: str
    easy_to_hide: bool = False
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
    place: str
    clue: str
    item: str
    name: str
    helper: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def make_setting(place: str) -> Setting:
    return _safe_lookup(SETTINGS, place)


def make_clue(clue_id: str) -> Clue:
    return _safe_lookup(CLUES, clue_id)


def make_item(item_id: str) -> WeddingItem:
    return _safe_lookup(ITEMS, item_id)


def reasonableness_gate(setting: Setting, clue: Clue, item: WeddingItem) -> bool:
    if item.importance == "critical" and clue.source not in {"ring_box", "pillow", "guest_table"}:
        return False
    return True


def _sound_finds(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("Detective")
    clue = _safe_fact(world, world.facts, "clue")
    if detective.memes.get("listening", 0) < THRESHOLD:
        return out
    if detective.memes.get("curiosity", 0) < THRESHOLD:
        return out
    sig = ("sound", clue.sound)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["certainty"] = detective.memes.get("certainty", 0) + 1
    out.append(f"{clue.sound}! That strange sound felt like a clue.")
    return out


def _reveal_item(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("Detective")
    clue = _safe_fact(world, world.facts, "clue")
    item = _safe_fact(world, world.facts, "item")
    if detective.memes.get("certainty", 0) < THRESHOLD:
        return out
    sig = ("reveal", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item_state = world.get(item.id)
    item_state.meters["found"] = 1
    out.append(f"The clue led straight to {item.phrase}.")
    return out


def _ending(world: World) -> list[str]:
    out: list[str] = []
    bride = world.get("Bride")
    groom = world.get("Groom")
    item = _safe_fact(world, world.facts, "item")
    if world.facts.get("resolved") and ("end",) not in world.fired:
        world.fired.add(("end",))
        bride.memes["relief"] = bride.memes.get("relief", 0) + 1
        groom.memes["relief"] = groom.memes.get("relief", 0) + 1
        out.append(
            f"With the {item.label} back in hand, the sleepy marriage could begin at last."
        )
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_sound_finds, _reveal_item, _ending):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, clue: Clue, item: WeddingItem, name: str, helper: str) -> World:
    world = World(setting)
    bride = world.add(Entity(id="Bride", kind="character", type="bride", label="the bride"))
    groom = world.add(Entity(id="Groom", kind="character", type="groom", label="the groom"))
    detective = world.add(Entity(
        id="Detective",
        kind="character",
        type="child",
        label=name,
        phrases="",
    ))
    helper_ent = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper,
        label=f"the {helper}",
    ))
    item_ent = world.add(Entity(
        id=item.id,
        kind="thing",
        type=item.type,
        label=item.label,
        phrase=item.phrase,
        owner=bride.id,
        caretaker=helper_ent.id,
    ))

    detective.memes["curiosity"] = 1
    detective.memes["listening"] = 1
    bride.memes["worry"] = 1
    groom.memes["worry"] = 1

    world.facts.update(
        clue=clue,
        item=item,
        detective=detective,
        bride=bride,
        groom=groom,
        helper=helper_ent,
    )

    world.say(
        f"It was a sleepy evening at {setting.place}, where the bride and groom were getting ready to marry."
    )
    world.say(
        f"{name} the little detective listened closely, because the quiet room kept making {clue.sound} sounds."
    )
    world.para()
    world.say(
        f"The bride frowned. Her {item.label} was missing, and without it the marriage did not feel complete."
    )
    world.say(
        f"{name} looked under chairs, behind flowers, and near the guest table, following the mystery one sound at a time."
    )
    propagate(world, narrate=True)
    world.para()
    world.say(
        f"At last, {name} found {item.phrase} tucked where {clue.reveal}."
    )
    world.say(
        f"The helper laughed softly, the bride smiled, and the groom held out his hand for the ceremony."
    )
    world.say(
        f"{clue.sound}! Then the happy ending came: the marriage was finished with hugs, cheers, and a peaceful yawn."
    )

    world.facts["resolved"] = True
    propagate(world, narrate=True)
    return world


SETTINGS = {
    "chapel": Setting(place="the old chapel", indoor=True, echo=True),
    "garden": Setting(place="the moonlit garden", indoor=False, echo=False),
    "hall": Setting(place="the little town hall", indoor=True, echo=False),
}

CLUES = {
    "tick": Clue(sound="tick-tick", source="clock", reveal="it had rolled behind a curtain", intensity="soft"),
    "creak": Clue(sound="creak-creak", source="door", reveal="it had slipped under a bench", intensity="thin"),
    "plink": Clue(sound="plink-plink", source="fountain", reveal="it had bounced into a flowerpot", intensity="bright"),
}

ITEMS = {
    "ring": WeddingItem(id="Ring", label="ring", phrase="the silver wedding ring", type="ring", importance="critical"),
    "pillow": WeddingItem(id="Pillow", label="pillow", phrase="the ring pillow", type="pillow", importance="important", easy_to_hide=True),
    "veil": WeddingItem(id="Veil", label="veil", phrase="the bride's veil", type="veil", importance="important"),
}

HELPERS = ["aunt", "uncle", "friend"]

NAMES = ["Mina", "Noah", "Ivy", "Theo", "Lena", "Arlo"]


@dataclass
class StoryParams:
    place: str
    clue: str
    item: str
    name: str
    helper: str
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
    out = []
    for place, setting in SETTINGS.items():
        for clue_id, clue in CLUES.items():
            for item_id, item in ITEMS.items():
                if reasonableness_gate(setting, clue, item):
                    out.append((place, clue_id, item_id))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    clue: Clue = _safe_fact(world, f, "clue")
    item: WeddingItem = _safe_fact(world, f, "item")
    detective: Entity = _safe_fact(world, f, "detective")
    return [
        f'Write a short mystery story for a small child that includes the sound effect "{clue.sound}".',
        f"Tell a sleepy wedding-day story where {detective.label} solves the missing {item.label} mystery.",
        f"Write a happy ending story set at {world.setting.place} about marriage, a clue, and a found {item.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    clue: Clue = _safe_fact(world, f, "clue")
    item: WeddingItem = _safe_fact(world, f, "item")
    detective: Entity = _safe_fact(world, f, "detective")
    bride: Entity = _safe_fact(world, f, "bride")
    groom: Entity = _safe_fact(world, f, "groom")
    helper: Entity = _safe_fact(world, f, "helper")
    return [
        QAItem(
            question=f"Who solved the mystery at {world.setting.place}?",
            answer=f"{detective.label} solved it by listening carefully and following the sound clues.",
        ),
        QAItem(
            question=f"What was missing from the sleepy marriage day?",
            answer=f"The {item.label} was missing, which worried the bride before the ceremony could begin.",
        ),
        QAItem(
            question=f"Why did everyone calm down at the end?",
            answer=f"Once {detective.label} found {item.phrase}, the bride, the groom, and the {helper.type} could smile and start the marriage happily.",
        ),
        QAItem(
            question=f"What sound kept coming up in the story?",
            answer=f"The story kept returning to {clue.sound}, which acted like a clue in the mystery.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    clue: Clue = _safe_fact(world, f, "clue")
    item: WeddingItem = _safe_fact(world, f, "item")
    return [
        QAItem(
            question="What is a marriage?",
            answer="A marriage is a wedding where two people promise to live as a family and care for each other.",
        ),
        QAItem(
            question="Why do detectives listen carefully in mysteries?",
            answer="Detectives listen carefully because tiny sounds and small details can point to the answer.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words like tick-tick or creak-creak that help readers hear the scene in their imagination.",
        ),
        QAItem(
            question="Why can a wedding feel sleepy and quiet?",
            answer="A wedding can feel sleepy and quiet when it is late, soft, and full of gentle voices instead of loud noise.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        if s.echo:
            lines.append(asp.fact("echo", pid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("sound", cid, c.sound))
        lines.append(asp.fact("source", cid, c.source))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("importance", iid, item.importance))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P,C,I) :- place(P), clue(C), item(I), not blocked(P,C,I).
blocked(P,C,I) :- indoor(P), source(C,door), importance(I,critical).
blocked(P,C,I) :- echo(P), source(C,clock), importance(I,critical).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Sleepy marriage mystery with sound effects and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = valid_combos()
    combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))]
    combos = [c for c in combos if (getattr(args, "clue", None) is None or c[1] == getattr(args, "clue", None))]
    combos = [c for c in combos if (getattr(args, "item", None) is None or c[2] == getattr(args, "item", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, clue, item = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    return StoryParams(place=place, clue=clue, item=item, name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        make_setting(params.place),
        make_clue(params.clue),
        make_item(params.item),
        params.name,
        params.helper,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="chapel", clue="creak", item="ring", name="Mina", helper="friend"),
    StoryParams(place="hall", clue="tick", item="pillow", name="Theo", helper="aunt"),
    StoryParams(place="garden", clue="plink", item="veil", name="Ivy", helper="uncle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for p, c, i in combos:
            print(f"  {p:8} {c:8} {i:8}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.name}: {p.clue} at {p.place} ({p.item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
