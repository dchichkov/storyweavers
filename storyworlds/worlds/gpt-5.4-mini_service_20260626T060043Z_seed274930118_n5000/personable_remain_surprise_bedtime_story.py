#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/personable_remain_surprise_bedtime_story.py
========================================================================================================================

A small bedtime-story world with a gentle surprise: a child tries to stay up,
but a kind, personable plan helps the night remain calm.

Seed premise:
---
A child gets ready for bed, but a surprise appears: a lost toy, a hidden note,
or a tiny bedtime wish. The surprise briefly wakes up big feelings, then a
lovely, reassuring routine helps everything remain safe, soft, and sleepy.

This world is designed to stay close to bedtime-story style:
- simple, child-facing prose
- warm, cozy setting
- a clear surprise beat
- a calm resolution that leaves the room peaceful

The model tracks physical "meters" and emotional "memes" as a tiny state
machine, and the prose is generated from that state.
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

    caregiver: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

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
    place: str = "the bedroom"
    detail: str = "A soft lamp glowed in the corner."
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
class Surprise:
    id: str
    label: str
    phrase: str
    kind: str
    gentle: bool = True
    makes: set[str] = field(default_factory=set)
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
class Comfort:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    reveal: str = ""
    calm_end: str = ""
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    setting: str
    surprise: str
    comfort: str
    name: str
    gender: str
    caregiver: str
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


SETTINGS = {
    "bedroom": Setting(
        place="the bedroom",
        detail="A soft lamp glowed in the corner, and the blanket waited like a cloud.",
        affords={"note", "toy", "star"},
    ),
    "nursery": Setting(
        place="the nursery",
        detail="The nursery was quiet, with a sleepy moon sticker on the wall.",
        affords={"note", "toy", "star"},
    ),
    "cabin": Setting(
        place="the little cabin room",
        detail="The cabin room was snug, and the window showed a silver moon.",
        affords={"note", "toy", "star"},
    ),
}

SURPRISES = {
    "note": Surprise(
        id="note",
        label="a tiny note",
        phrase="a tiny folded note under the pillow",
        kind="note",
        gentle=True,
        makes={"wonder"},
    ),
    "toy": Surprise(
        id="toy",
        label="a lost toy",
        phrase="the missing plush toy in the blanket fold",
        kind="toy",
        gentle=True,
        makes={"worry", "joy"},
    ),
    "star": Surprise(
        id="star",
        label="a paper star",
        phrase="a paper star taped to the lamp",
        kind="star",
        gentle=True,
        makes={"wonder", "joy"},
    ),
}

COMFORTS = {
    "hug": Comfort(
        id="hug",
        label="a warm hug",
        phrase="a warm hug and a slow breath",
        helps={"worry", "wonder"},
        reveal="They took a slow breath together and read the note again.",
        calm_end="Soon the room felt quiet again.",
    ),
    "song": Comfort(
        id="song",
        label="a lullaby",
        phrase="a soft lullaby",
        helps={"worry", "wonder", "joy"},
        reveal="Then a soft lullaby made the surprise feel friendly and small.",
        calm_end="Soon the room felt like a nest again.",
    ),
    "light": Comfort(
        id="night light",
        label="the night light",
        phrase="the night light turned low",
        helps={"worry"},
        reveal="With the night light turned low, the surprise looked gentle instead of strange.",
        calm_end="Soon the shadows stayed soft and calm.",
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Ava", "Zoe", "Nora", "Ella", "Maya", "Ivy"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Eli", "Noah", "Sam", "Max", "Ben"]
TRAITS = ["personable", "curious", "gentle", "cheerful", "sleepy", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for surprise_id in setting.affords:
            for comfort_id in COMFORTS:
                combos.append((setting_id, surprise_id, comfort_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cozy bedtime surprise story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--caregiver", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "surprise", None) is None or c[1] == getattr(args, "surprise", None))
              and (getattr(args, "comfort", None) is None or c[2] == getattr(args, "comfort", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, surprise, comfort = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    caregiver = getattr(args, "caregiver", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, surprise=surprise, comfort=comfort, name=name, gender=gender, caregiver=caregiver, trait=trait)


def set_meter(ent: Entity, key: str, value: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + value


def set_meme(ent: Entity, key: str, value: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + value


def predict(world: World, hero: Entity, surprise: Surprise) -> dict:
    sim = world.copy()
    h = sim.get(hero.id)
    if surprise.kind == "toy":
        set_meme(h, "worry", 1)
        set_meme(h, "joy", 1)
    else:
        set_meme(h, "wonder", 1)
    return {
        "worry": h.memes.get("worry", 0),
        "joy": h.memes.get("joy", 0),
    }


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a {hero.memes.get('trait', 'personable')} little {hero.type} who liked quiet nights.")


def bedtime_setup(world: World, hero: Entity, caregiver: Entity, surprise: Surprise) -> None:
    world.say(f"It was bedtime in {world.setting.place}, and {world.setting.detail}")
    world.say(f"{hero.id} had already brushed {hero.pronoun('possessive')} teeth and hugged {hero.pronoun('possessive')} {caregiver.noun()} goodnight.")
    world.say(f"Then {hero.id} found {surprise.phrase}.")
    if surprise.kind == "toy":
        set_meme(hero, "worry", 1)
    else:
        set_meme(hero, "wonder", 1)


def surprise_turn(world: World, hero: Entity, caregiver: Entity, surprise: Surprise) -> None:
    if surprise.kind == "toy":
        world.say(f"{hero.id}'s eyes grew wide, because the toy had been missing all day.")
        world.say(f"{hero.pronoun().capitalize()} wanted to hold {surprise.label} forever, even though sleep was waiting.")
    elif surprise.kind == "note":
        world.say(f"{hero.id} opened {surprise.label} very carefully.")
        world.say(f"The note was short and sweet: 'You are loved. Sleep well.'")
    else:
        world.say(f"{hero.id} smiled at the paper star.")
        world.say(f"It was a small surprise, but it made the room feel extra kind.")


def comfort_move(world: World, caregiver: Entity, hero: Entity, surprise: Surprise, comfort: Comfort) -> None:
    set_meme(hero, "calm", 1)
    if "worry" in hero.memes and hero.memes["worry"] >= THRESHOLD:
        set_meme(hero, "worry", -1)
    if "wonder" in hero.memes and hero.memes["wonder"] >= THRESHOLD:
        set_meme(hero, "wonder", -1)
    world.say(f"{caregiver.pronoun('possessive').capitalize()} {caregiver.noun()} offered {comfort.phrase}.")
    world.say(comfort.reveal)


def resolution(world: World, hero: Entity, caregiver: Entity, surprise: Surprise, comfort: Comfort) -> None:
    set_meter(hero, "sleepy", 1)
    if surprise.kind == "toy":
        world.say(f"{hero.id} tucked the little toy beside the pillow so it could remain safe until morning.")
    elif surprise.kind == "note":
        world.say(f"{hero.id} placed the note on the nightstand so the kind words could remain close.")
    else:
        world.say(f"{hero.id} left the paper star where it was, shining softly above the bed.")
    world.say(f"{hero.id} yawned, and {caregiver.pronoun('possessive')} {caregiver.noun()} smiled at the sleepy face.")
    world.say(comfort.calm_end)
    world.say(f"At last, the surprise remained, but the room had become quiet, cozy, and ready for dreams.")


def tell(setting: Setting, surprise: Surprise, comfort: Comfort, hero_name: str,
         hero_type: str, caregiver_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={"trait": trait}))
    caregiver = world.add(Entity(id="Caregiver", kind="character", type=caregiver_type, label="parent", meters={}, memes={}))
    world.facts["hero"] = hero
    world.facts["caregiver"] = caregiver
    world.facts["surprise"] = surprise
    world.facts["comfort"] = comfort

    introduce(world, hero)
    world.para()
    bedtime_setup(world, hero, caregiver, surprise)
    surprise_turn(world, hero, caregiver, surprise)
    world.para()
    comfort_move(world, caregiver, hero, surprise, comfort)
    resolution(world, hero, caregiver, surprise, comfort)

    world.facts["calm"] = hero.memes.get("calm", 0) >= THRESHOLD
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    surprise: Surprise = _safe_fact(world, f, "surprise")
    comfort: Comfort = _safe_fact(world, f, "comfort")
    return [
        f"Write a bedtime story for a small child where {hero.id} finds {surprise.phrase} and stays calm.",
        f"Tell a gentle, personable bedtime tale that includes the word 'remain' and ends with {comfort.label}.",
        f"Write a cozy story about a surprise at bedtime that helps {hero.id} feel sleepy again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    caregiver: Entity = _safe_fact(world, world.facts, "caregiver")
    surprise: Surprise = _safe_fact(world, world.facts, "surprise")
    comfort: Comfort = _safe_fact(world, world.facts, "comfort")
    trait = hero.memes.get("trait", "personable")
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a {trait} little {hero.type}, and {caregiver.pronoun('possessive')} {caregiver.noun()} at bedtime.",
        ),
        QAItem(
            question=f"What surprise did {hero.id} find?",
            answer=f"{hero.id} found {surprise.phrase}.",
        ),
        QAItem(
            question=f"What helped the room remain calm?",
            answer=f"{comfort.phrase} helped {hero.id} settle down, so the room could remain soft and peaceful.",
        ),
    ]
    if world.facts.get("calm"):
        qa.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt sleepy and safe at the end, and the surprise remained in the room without spoiling bedtime.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bedtime?",
            answer="Bedtime is the time when children get ready to rest, cuddle up, and fall asleep for the night.",
        ),
        QAItem(
            question="What does a lullaby do?",
            answer="A lullaby is a soft song that helps a child relax and feel sleepy.",
        ),
        QAItem(
            question="Why can a surprise feel exciting?",
            answer="A surprise can feel exciting because it is unexpected and makes you wonder what will happen next.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id} ({e.type}) meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- setting_fact(S).
surprise(S) :- surprise_fact(S).
comfort(C) :- comfort_fact(C).
valid(Setting, Surprise, Comfort) :- setting_fact(Setting), surprise_fact(Surprise), comfort_fact(Comfort).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting_fact", sid))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise_fact", sid))
    for cid in COMFORTS:
        lines.append(asp.fact("comfort_fact", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python.")
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    if py - cl:
        print("only in python:", sorted(py - cl))
    return 1


def explain_rejection() -> str:
    return "No valid bedtime surprise combination matches the given options."


CURATED = []  # placeholder to satisfy linters? no, must avoid placeholders.

CURATED = [
    StoryParams(setting="bedroom", surprise="note", comfort="hug", name="Mia", gender="girl", caregiver="mother", trait="personable"),
    StoryParams(setting="nursery", surprise="toy", comfort="song", name="Leo", gender="boy", caregiver="father", trait="gentle"),
    StoryParams(setting="cabin", surprise="star", comfort="light", name="Nora", gender="girl", caregiver="mother", trait="curious"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "setting", None) and getattr(args, "surprise", None) and (getattr(args, "setting", None), getattr(args, "surprise", None)) not in [(s, su) for s, su, _ in valid_combos()]:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "surprise", None) is None or c[1] == getattr(args, "surprise", None))
              and (getattr(args, "comfort", None) is None or c[2] == getattr(args, "comfort", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, surprise, comfort = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    caregiver = getattr(args, "caregiver", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, surprise=surprise, comfort=comfort, name=name, gender=gender, caregiver=caregiver, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(SURPRISES, params.surprise), _safe_lookup(COMFORTS, params.comfort),
                 params.name, params.gender, params.caregiver, params.trait)
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
        print(asp_program("#show valid/3."))
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.surprise} in {p.setting} ({p.comfort})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
