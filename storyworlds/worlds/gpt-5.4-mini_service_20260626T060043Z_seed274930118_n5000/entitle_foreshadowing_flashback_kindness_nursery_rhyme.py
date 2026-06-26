#!/usr/bin/env python3
"""
storyworlds/worlds/entitle_foreshadowing_flashback_kindness_nursery_rhyme.py
============================================================================

A small story world with a nursery-rhyme feel: a child, a desired prize,
a gentle warning, a flashback to past kindness, and a softened ending.

Seed tale:
---
A tiny child wants a shiny bell all to themself. The bell is meant for the
village song, but the child feels entitled to keep it. A caregiver notices a
storm cloud, remembers a time the child shared a spoon in the rain, and uses
that memory to guide the child toward kindness. In the end, the bell is lent
out, the song is shared, and the cloud passes by.

World model:
---
    desire for prize            -> joy + entitlement +1
    warning with foreshadowing   -> fear +1, tension +1
    flashback to kindness        -> memory +1, shame softens, kindness rises
    sharing compromise           -> entitlement -> 0, joy + love +1, tension -> 0
    refusing kindness            -> tension remains, ending is less warm

The prose is written in a nursery-rhyme style with simple beats and a small
amount of rhyme and repetition, but the state still drives what is narrated.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    carer: object | None = None
    hero: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        for k in ("brightness", "wetness", "mud", "safety", "shared"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "love", "fear", "tension", "kindness", "entitlement", "memory", "shame"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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


@dataclass
class Setting:
    place: str = "the village green"
    mood: str = "bright"
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
class Prize:
    label: str
    phrase: str
    type: str
    owner_role: str
    shared_use: str
    keyword: str
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
    prize: str
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _r_foreshadow(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["fear"] < THRESHOLD:
            continue
        sig = ("foreshadow", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.facts["foreshadowed"] = True
        out.append("A little dark cloud came drifting by, as if it knew a choice was near.")
    return out


def _r_flashback(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["memory"] < THRESHOLD:
            continue
        sig = ("flashback", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append("There was a remembery time, not long ago, when a kind deed shone bright.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["kindness"] < THRESHOLD:
            continue
        sig = ("kindness", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["tension"] = max(0.0, ent.memes["tension"] - 1.0)
        out.append("Kind hands make hard hearts soften, like butter in the sun.")
    return out


CAUSAL_RULES = [
    _r_foreshadow,
    _r_flashback,
    _r_kindness,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def title_case(s: str) -> str:
    return s[:1].upper() + s[1:]


def build_story(world: World, hero: Entity, caregiver: Entity, prize: Entity) -> None:
    day = world.setting.mood
    world.say(f"{hero.id} was a {hero.type} with {hero.label_word if hasattr(hero, 'label_word') else hero.type} cheeks and a bright small grin.")
    world.say(f"{hero.pronoun().capitalize()} loved the {prize.label}, for it jingled like a happy little song.")
    world.say(f"On the {world.setting.place}, {hero.id} wanted the {prize.label} all for {hero.pronoun('object')} own.")

    hero.memes["joy"] += 1
    hero.memes["entitlement"] += 1
    prize.meters["shared"] += 1

    world.para()
    world.say(f"But {caregiver.id} saw the sky go gray in a blink and heard a soft patter on the way.")
    hero.memes["fear"] += 1
    hero.memes["tension"] += 1
    propagate(world)

    world.say(f"\"If we keep the {prize.label} alone,\" said {caregiver.id}, \"the song will miss its tune.\"")
    world.say(f"{hero.id} frowned, for {hero.pronoun('possessive')} heart was tangled in a selfish little frown.")

    world.para()
    hero.memes["memory"] += 1
    world.say(f"Then came a flash of yesteryear: {hero.id} once shared a spoon in rain and fear.")
    propagate(world)
    world.say(f"Back then, {caregiver.id} had laughed and dried {hero.pronoun('object')} coat, and that kindness stayed afloat.")

    if prize.keyword == "bell":
        world.say(f"The bell was for the village song, for many voices to carry along.")
    else:
        world.say(f"The {prize.label} was meant to be used with care, so friends could find their share.")

    hero.memes["kindness"] += 1
    if hero.memes["entitlement"] >= THRESHOLD:
        world.say(f"{hero.id} held the {prize.label}, then let it rest in {caregiver.pronoun('possessive')} hand.")
    propagate(world)

    world.para()
    hero.memes["entitlement"] = 0.0
    hero.memes["tension"] = 0.0
    hero.memes["love"] += 1
    hero.memes["joy"] += 1
    prize.meters["shared"] = 1.0

    world.say(f"\"Take it for the song,\" {hero.id} said, \"and I will sing along.\"")
    world.say(f"So {hero.id} shared the {prize.label}, and the little cloud went swish right by.")
    world.say(f"The village heard a merry ring, and the day stayed warm beneath the sky.")

    world.facts.update(hero=hero, caregiver=caregiver, prize=prize)


SETTINGS = {
    "green": Setting(place="the village green", mood="bright", affords={"share_song"}),
    "garden": Setting(place="the cottage garden", mood="soft", affords={"share_song"}),
    "meadow": Setting(place="the clover meadow", mood="gentle", affords={"share_song"}),
}

PRIZES = {
    "bell": Prize(
        label="silver bell",
        phrase="a silver bell for the village song",
        type="bell",
        owner_role="the songkeeper",
        shared_use="ring in the chorus",
        keyword="bell",
    ),
    "ribbon": Prize(
        label="blue ribbon",
        phrase="a blue ribbon for the maypole dance",
        type="ribbon",
        owner_role="the dancer",
        shared_use="tie for the dance",
        keyword="ribbon",
    ),
    "basket": Prize(
        label="berry basket",
        phrase="a berry basket for the morning market",
        type="basket",
        owner_role="the gatherer",
        shared_use="carry the berries together",
        keyword="basket",
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nina", "Maya", "Poppy", "Daisy"]
BOY_NAMES = ["Tom", "Ben", "Oli", "Jack", "Finn", "Robin"]
TRAITS = ["merry", "tiny", "spry", "cheery", "wily", "curious"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, prize) for place in SETTINGS for prize in PRIZES]


@dataclass
class StoryState:
    place: str
    prize: str
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


def _gender_ok(prize: Prize, gender: str) -> bool:
    return True


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world about entitlement, foreshadowing, flashback, and kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "prize", None) is None or c[1] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, prize = rng.choice(list(combos))
    p = _safe_lookup(PRIZES, prize)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    caregiver = getattr(args, "caregiver", None) or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, prize=prize, name=name, gender=gender, caregiver=caregiver, trait=trait)


def make_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.trait))
    carer = world.add(Entity(id=params.caregiver.title(), kind="character", type=params.caregiver))
    prize = world.add(Entity(id=params.prize, type=params.prize, label=_safe_lookup(PRIZES, params.prize).label, phrase=_safe_lookup(PRIZES, params.prize).phrase, owner=hero.id, caretaker=carer.id))
    build_story(world, hero, carer, prize)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    prize = _safe_fact(world, f, "prize")
    return [
        f"Write a nursery-rhyme style story about {hero.id} and the {prize.label} with a gentle turn toward kindness.",
        f"Tell a short child-friendly tale where a child feels entitled to keep a {prize.label}, then learns to share.",
        "Write a simple rhyme with foreshadowing, a flashback, and a warm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    carer = world.get(next(e.id for e in world.characters() if e.id != hero.id))
    prize = _safe_fact(world, f, "prize")
    return [
        QAItem(question=f"What did {hero.id} want at the start?", answer=f"{hero.id} wanted the {prize.label} all for {hero.pronoun('object')} own."),
        QAItem(question=f"What warning did {carer.id} notice in the sky?", answer="A dark cloud came drifting by, so the caregiver warned that a storm might come."),
        QAItem(question=f"What old memory helped {hero.id} change?", answer=f"{hero.id} remembered a time {hero.pronoun('subject')} shared a spoon in the rain, and that kindness helped {hero.pronoun('object')} choose better."),
        QAItem(question=f"How did the story end?", answer=f"{hero.id} shared the {prize.label}, and the little cloud passed by as the song rang out."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    prize = _safe_fact(world, f, "prize")
    if prize.keyword == "bell":
        return [QAItem(question="What is a bell for?", answer="A bell makes a clear ringing sound, and people can use it to call attention or make music.")]
    if prize.keyword == "ribbon":
        return [QAItem(question="What is a ribbon for?", answer="A ribbon is a long, soft strip of fabric used for decorating, tying, or dancing.")]
    return [QAItem(question="What is a basket for?", answer="A basket is a container with sides, used for carrying things like fruit or flowers.")]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(out)


CURATED = [
    StoryParams(place="green", prize="bell", name="Mina", gender="girl", caregiver="mother", trait="merry"),
    StoryParams(place="garden", prize="ribbon", name="Tom", gender="boy", caregiver="aunt", trait="curious"),
    StoryParams(place="meadow", prize="basket", name="Lily", gender="girl", caregiver="father", trait="cheery"),
]


ASP_RULES = r"""
valid_story(Place, Prize) :- place(Place), prize(Prize).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for prize in PRIZES:
        lines.append(asp.fact("prize", prize))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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
        print("\n".join(f"{a} {b}" for a, b in asp_valid_combos()))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.prize} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
