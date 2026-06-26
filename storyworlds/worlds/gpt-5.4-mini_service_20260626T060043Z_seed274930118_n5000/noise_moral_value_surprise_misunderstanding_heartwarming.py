#!/usr/bin/env python3
"""
storyworlds/worlds/noise_moral_value_surprise_misunderstanding_heartwarming.py
==============================================================================

A small heartwarming storyworld about noise, a misunderstanding, and a gentle
moral-value turn: a child makes too much noise, someone misreads the situation,
and the family finds a kind way to fix it.

Seed tale sketch:
---
A little child loves making music with a noisy toy. In a quiet place, the sound
startles a helper, who thinks the child is being rude. The child feels sad when
the toy is taken away, but then the child notices that the helper is actually
trying to protect someone resting nearby. The child lowers the noise, offers an
apology, and uses the toy in a softer way. Everyone feels better, and the story
ends with peace, warmth, and a small lesson about thinking before judging.

World model:
- physical meters: sound, tiredness, distance, calmness
- emotional memes: joy, hurt, confusion, trust, kindness, embarrassment, relief
- narrative instruments:
  * noise: the toy can raise sound
  * misunderstanding: an observer can misread the intent
  * surprise: a quiet reveal changes the meaning of the scene
  * moral value: kindness, apology, and care improve the ending

This script is standalone and uses only stdlib plus the shared Storyweavers
result containers. ASP support is included inline as the declarative twin of the
reasonableness gate.
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

METER_THRESHOLD = 1.0
MEME_THRESHOLD = 1.0



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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    observer: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_word(self) -> str:
        return self.label or self.id

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
    quiet: bool = True
    hides_resting_person: bool = False
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
class NoiseToy:
    id: str
    label: str
    phrase: str
    sound_kind: str
    softness: str
    can_be_soft: bool
    surprise: str
    moral: str
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
class QuietAid:
    id: str
    label: str
    phrase: str
    helps: set[str]
    prep: str
    tail: str
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    toy: str
    aid: str
    name: str
    gender: str
    observer: str
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
    "nap_room": Setting(place="the nap room", quiet=True, hides_resting_person=True, affords={"noise"}),
    "reading_corner": Setting(place="the reading corner", quiet=True, hides_resting_person=True, affords={"noise"}),
    "train_car": Setting(place="the train car", quiet=True, hides_resting_person=True, affords={"noise"}),
}

TOYS = {
    "drum": NoiseToy(
        id="drum",
        label="a tiny drum",
        phrase="a tiny drum with a bright red strap",
        sound_kind="banging",
        softness="softly tapping",
        can_be_soft=True,
        surprise="it was only a practice drum and not a toy for trouble",
        moral="kindness matters more than being right too fast",
        tags={"noise", "music", "drum"},
    ),
    "bell": NoiseToy(
        id="bell",
        label="a jingling bell",
        phrase="a jingling bell on a ribbon",
        sound_kind="jingling",
        softness="carefully jingling",
        can_be_soft=True,
        surprise="it was a gift meant to help everyone take turns and listen",
        moral="listening first can save a lot of hurt feelings",
        tags={"noise", "music", "bell"},
    ),
    "rattle": NoiseToy(
        id="rattle",
        label="a shiny rattle",
        phrase="a shiny rattle with little stars on it",
        sound_kind="rattling",
        softness="gently shaking",
        can_be_soft=True,
        surprise="the rattles sounded loud only because the room was so quiet",
        moral="a small act can feel big in the wrong moment",
        tags={"noise", "baby", "rattle"},
    ),
}

QUIET_AIDS = {
    "blanket": QuietAid(
        id="blanket",
        label="a soft blanket",
        phrase="a soft blanket for the sleeping guest",
        helps={"sound"},
        prep="cover the toy with a soft blanket and sit close by",
        tail="covered the toy and played beside the blanket",
        tags={"quiet", "blanket"},
    ),
    "pillow": QuietAid(
        id="pillow",
        label="a fluffy pillow",
        phrase="a fluffy pillow to muffle the sound",
        helps={"sound"},
        prep="wrap the toy in a fluffy pillow for a little while",
        tail="wrapped the toy and made the room hush",
        tags={"quiet", "pillow"},
    ),
    "curtain": QuietAid(
        id="curtain",
        label="the thick curtain",
        phrase="the thick curtain near the window",
        helps={"sound"},
        prep="move behind the thick curtain and keep the sound low",
        tail="moved behind the curtain and tried the toy again",
        tags={"quiet", "curtain"},
    ),
}

GENDER_NAMES = {
    "girl": ["Mina", "Luna", "Nora", "Ivy", "Maya", "Ruby"],
    "boy": ["Owen", "Theo", "Ben", "Eli", "Noah", "Finn"],
}

OBSERVER_NAMES = ["Grandma", "Grandpa", "Aunt June", "Mr. Lee", "Mrs. Bell", "Ms. Ada"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for toy_id in setting.affords:
            for aid_id in QUIET_AIDS:
                if story_reasonable(_safe_lookup(TOYS, toy_id), _safe_lookup(QUIET_AIDS, aid_id), setting):
                    combos.append((place, toy_id, aid_id))
    return combos


def story_reasonable(toy: NoiseToy, aid: QuietAid, setting: Setting) -> bool:
    return "sound" in aid.helps and setting.quiet and setting.hides_resting_person and toy.can_be_soft


def explain_rejection(toy: NoiseToy, aid: QuietAid, setting: Setting) -> str:
    return (
        f"(No story: {toy.label} and {aid.label} don't make a convincing gentle fix "
        f"in {setting.place}. The setup needs a toy that can be softened and a quiet aid "
        f"that can really lower the sound.)"
    )


def introduce(world: World, child: Entity, toy: NoiseToy) -> None:
    world.say(
        f"{child.name_word()} was a little {child.type} who loved {toy.label} and the brave, bright sounds it made."
    )
    world.say(
        f"{child.pronoun().capitalize()} carried {toy.phrase} everywhere and smiled whenever {toy.sound_kind} filled the air."
    )


def setup_scene(world: World, child: Entity, observer: Entity, toy: NoiseToy) -> None:
    world.say(
        f"One quiet day, {child.name_word()} went to {world.setting.place} with {child.pronoun('possessive')} {toy.label}."
    )
    world.say(
        f"Near a little resting spot, {observer.name_word()} was trying to help someone sleep."
    )


def make_noise(world: World, child: Entity, toy: NoiseToy) -> None:
    child.meters["sound"] += 1
    child.memes["joy"] += 1
    world.say(
        f"{child.name_word()} began {toy.softness}, and soon the room filled with {toy.sound_kind}."
    )


def observer_misunderstands(world: World, observer: Entity, child: Entity, toy: NoiseToy) -> None:
    observer.memes["confusion"] += 1
    observer.memes["concern"] += 1
    child.memes["embarrassment"] += 1
    world.say(
        f"{observer.name_word()} frowned and thought {child.name_word()} was being careless on purpose."
    )
    world.say(
        f"{observer.name_word()} asked {child.name_word()} to stop, and {child.name_word()} felt a hot little sting of hurt."
    )


def reveal_misunderstanding(world: World, observer: Entity, child: Entity, toy: NoiseToy) -> None:
    observer.memes["confusion"] += 1
    world.say(
        f"Then {child.name_word()} pointed to the sleeping guest and explained that {toy.surprise}."
    )
    world.say(
        f"{observer.name_word()} blinked, because the loud sound had seemed rude before, but now it looked like a mistake, not meanness."
    )


def choose_kind_fix(world: World, child: Entity, observer: Entity, aid: QuietAid, toy: NoiseToy) -> None:
    child.memes["kindness"] += 1
    child.memes["trust"] += 1
    observer.memes["relief"] += 1
    child.meters["sound"] = max(0.0, child.meters["sound"] - 1.0)
    world.say(
        f"{child.name_word()} said sorry, then {aid.prep}."
    )
    world.say(
        f"{observer.name_word()} softened right away, because {toy.moral}."
    )
    world.say(
        f"Soon {child.name_word()} was {toy.softness} again, and {aid.tail}."
    )


def ending_image(world: World, child: Entity, observer: Entity, toy: NoiseToy) -> None:
    child.memes["joy"] += 1
    child.memes["relief"] += 1
    observer.memes["trust"] += 1
    world.say(
        f"At the end, the little sound stayed gentle, the resting guest kept sleeping, and {child.name_word()} and {observer.name_word()} shared a warm smile."
    )


def tell(setting: Setting, toy: NoiseToy, aid: QuietAid, child_name: str, gender: str, observer_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=gender))
    observer = world.add(Entity(id=observer_name, kind="character", type="adult"))
    world.add(Entity(id=toy.id, type="toy", label=toy.label, phrase=toy.phrase, owner=child.id))
    world.add(Entity(id=aid.id, type="aid", label=aid.label, phrase=aid.phrase, caretaker=observer.id, protective=True))

    introduce(world, child, toy)
    world.para()
    setup_scene(world, child, observer, toy)
    make_noise(world, child, toy)
    observer_misunderstands(world, observer, child, toy)
    world.para()
    reveal_misunderstanding(world, observer, child, toy)
    choose_kind_fix(world, child, observer, aid, toy)
    ending_image(world, child, observer, toy)

    world.facts.update(
        child=child,
        observer=observer,
        toy=toy,
        aid=aid,
        setting=setting,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    toy = _safe_fact(world, f, "toy")
    aid = _safe_fact(world, f, "aid")
    observer = _safe_fact(world, f, "observer")
    return [
        f'Write a heartwarming story about {child.name_word()} and a noisy toy in {world.setting.place}.',
        f"Tell a gentle story where {child.name_word()} makes too much noise, {observer.name_word()} misunderstands, and they solve it kindly with {aid.label}.",
        f'Write a short child-friendly story that includes "{toy.label}" and ends with a warm apology and a calm room.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    observer = _safe_fact(world, f, "observer")
    toy = _safe_fact(world, f, "toy")
    aid = _safe_fact(world, f, "aid")
    place = world.setting.place
    return [
        QAItem(
            question=f"Who was the story about in {place}?",
            answer=f"The story was about {child.name_word()}, a little {child.type} who loved {toy.label}.",
        ),
        QAItem(
            question=f"Why did {observer.name_word()} first get upset with {child.name_word()}?",
            answer=f"{observer.name_word()} thought {child.name_word()} was being careless because the {toy.label} made a lot of noise near someone who needed rest.",
        ),
        QAItem(
            question=f"How did {child.name_word()} help make things better?",
            answer=f"{child.name_word()} apologized, lowered the sound, and used {aid.label} so the play could stay gentle.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the misunderstanding was fixed, the room was quieter, and {child.name_word()} and {observer.name_word()} felt warm and calm together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    toy = _safe_fact(world, f, "toy")
    aid = _safe_fact(world, f, "aid")
    return [
        QAItem(
            question="What is noise?",
            answer="Noise is sound that can be loud, sharp, or hard to ignore.",
        ),
        QAItem(
            question="What does a blanket do in a quiet room?",
            answer="A soft blanket can help muffle sound and make a noisy thing less loud.",
        ),
        QAItem(
            question=f"Why can a person misunderstand a noisy toy?",
            answer="A person can misunderstand when they hear the sound but do not yet know the reason behind it.",
        ),
        QAItem(
            question=f"What is the good lesson in a story with {toy.label} and {aid.label}?",
            answer="The good lesson is to think kindly before judging, and to fix mistakes with apology and care.",
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
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="nap_room", toy="drum", aid="blanket", name="Mina", gender="girl", observer="Grandma"),
    StoryParams(place="reading_corner", toy="bell", aid="pillow", name="Owen", gender="boy", observer="Mrs. Bell"),
    StoryParams(place="train_car", toy="rattle", aid="curtain", name="Luna", gender="girl", observer="Mr. Lee"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming storyworld about noise, misunderstanding, and kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--aid", choices=QUIET_AIDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--observer", choices=OBSERVER_NAMES)
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
    if getattr(args, "place", None) or getattr(args, "toy", None) or getattr(args, "aid", None) or getattr(args, "gender", None):
        combos = [
            c for c in combos
            if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
            and (getattr(args, "toy", None) is None or c[1] == getattr(args, "toy", None))
            and (getattr(args, "aid", None) is None or c[2] == getattr(args, "aid", None))
        ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, toy_id, aid_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(GENDER_NAMES, gender))
    observer = getattr(args, "observer", None) or rng.choice(OBSERVER_NAMES)
    if getattr(args, "toy", None) and getattr(args, "aid", None):
        if not story_reasonable(_safe_lookup(TOYS, getattr(args, "toy", None)), _safe_lookup(QUIET_AIDS, getattr(args, "aid", None)), _safe_lookup(SETTINGS, place)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, toy=toy_id, aid=aid_id, name=name, gender=gender, observer=observer)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TOYS, params.toy), _safe_lookup(QUIET_AIDS, params.aid), params.name, params.gender, params.observer)
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
reason(place, toy, aid) :- setting(place), toy(toy), aid(aid), quiet(place), hides_resting(place),
                           can_be_soft(toy), helps_sound(aid).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.quiet:
            lines.append(asp.fact("quiet", pid))
        if s.hides_resting_person:
            lines.append(asp.fact("hides_resting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, t in TOYS.items():
        lines.append(asp.fact("toy", tid))
        if t.can_be_soft:
            lines.append(asp.fact("can_be_soft", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tag))
    for aid, a in QUIET_AIDS.items():
        lines.append(asp.fact("aid", aid))
        for h in sorted(a.helps):
            lines.append(asp.fact("helps_sound", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reason/3."))
    return sorted(set(asp.atoms(model, "reason")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show reason/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
