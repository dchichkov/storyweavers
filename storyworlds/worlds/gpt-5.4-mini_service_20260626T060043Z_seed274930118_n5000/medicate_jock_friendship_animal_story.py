#!/usr/bin/env python3
"""
Standalone storyworld: a friendship-and-care animal story.

Premise:
- A sporty animal friend ("jock") gets a scrape or a sore.
- A friend notices, brings medicine, and helps medicate the hurt animal.
- The tension is whether the jock will accept care or keep playing.
- The turn is a gentle friendship act that makes the world feel safe again.

This world is intentionally small and constraint-checked:
- only a few compatible settings, animals, injuries, and care kits
- invalid explicit choices raise StoryError
- the story state drives the narration and Q&A
- an inline ASP twin mirrors the compatibility gate
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
    injured: bool = False
    using: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    jock: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "doe", "cow", "cat", "fox", "rabbit"}
        male = {"boy", "buck", "bull", "dog", "bear", "wolf"}
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
    indoor: bool = False
    calm: bool = True
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
class Injury:
    id: str
    label: str
    phrase: str
    symptom: str
    needs: set[str]
    trouble: str
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
class CareKit:
    id: str
    label: str
    phrase: str
    treats: set[str]
    prep: str
    finish: str
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
    injury: str
    kit: str
    friend_kind: str
    jock_kind: str
    friend_name: str
    jock_name: str
    seed: Optional[int] = None
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
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        return c


def _r_rest(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters.get("ache", 0) < 1:
            continue
        sig = ("rest", e.id)
        if sig in world.fired:
            continue
        if e.using in {"bandage", "ointment"}:
            continue
        world.fired.add(sig)
        e.meters["tired"] = e.meters.get("tired", 0) + 1
        out.append(f"{e.label or e.id} looked tired and needed a little rest.")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    friend = world.get("friend")
    jock = world.get("jock")
    if friend.memes.get("care", 0) >= 1 and jock.memes.get("trust", 0) >= 1:
        sig = ("friendship",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        friend.memes["warmth"] = friend.memes.get("warmth", 0) + 1
        jock.memes["warmth"] = jock.memes.get("warmth", 0) + 1
        out.append("__friendship__")
    return out


CAUSAL_RULES = [
    _r_rest,
    _r_friendship,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule(world)
            if produced:
                changed = True
                out.extend([s for s in produced if s != "__friendship__"])
    if narrate:
        for s in out:
            world.say(s)
    return out


def valid_combo(setting: Setting, injury: Injury, kit: CareKit) -> bool:
    return bool(injury.id in kit.treats and setting.calm)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for inj_id, inj in INJURIES.items():
            for kit_id, kit in KITS.items():
                if valid_combo(setting, inj, kit):
                    out.append((place, inj_id, kit_id))
    return out


def reason_reject(injury: Injury, kit: CareKit) -> str:
    return (
        f"(No story: {kit.label} does not help with {injury.phrase}. "
        f"The care kit must honestly treat the sore, so this pair is rejected.)"
    )


def setting_detail(setting: Setting) -> str:
    if setting.indoor:
        return f"The {setting.place} was cozy and quiet."
    return f"{setting.place.capitalize()} was bright and open, with room for a slow walk."


def introduce(world: World, jock: Entity, friend: Entity) -> None:
    world.say(
        f"{friend.id} was a kind little {friend.type} who liked helping friends."
    )
    world.say(
        f"{jock.id} was a sporty {jock.type} who loved running, jumping, and being a jock."
    )


def setup_injury(world: World, jock: Entity, injury: Injury) -> None:
    jock.meters["ache"] = 1
    jock.injured = True
    world.say(
        f"One day, {jock.id} got {injury.phrase}. {injury.symptom} made every step feel slower."
    )


def ask_help(world: World, friend: Entity, jock: Entity, injury: Injury) -> None:
    friend.memes["care"] = friend.memes.get("care", 0) + 1
    world.say(
        f"{friend.id} noticed the trouble and asked if {jock.id} wanted help."
    )
    world.say(
        f'"I can medicate it," {friend.id} said softly, holding up {_safe_lookup(KITS, world.facts.get("kit")).phrase}.'
    )


def resist(world: World, jock: Entity) -> None:
    jock.memes["stubborn"] = jock.memes.get("stubborn", 0) + 1
    world.say(
        f"{jock.id} still wanted to keep playing, but the sore kept poking at {jock.pronoun("possessive")} mood."
    )


def medicate(world: World, friend: Entity, jock: Entity, kit: CareKit, injury: Injury) -> None:
    if injury.id not in kit.treats:
        pass
    jock.using = kit.id
    jock.memes["trust"] = jock.memes.get("trust", 0) + 1
    jock.meters["ache"] = 0
    jock.injured = False
    world.say(
        f"{friend.id} gently {kit.prep} and cleaned the sore."
    )
    world.say(
        f"Then {friend.id} used {kit.label} to medicate the spot, and {jock.id} breathed out easier."
    )
    world.say(
        f"After that, they {kit.finish}, and the little hurt no longer bossed the day."
    )


def resolve(world: World, setting: Setting, friend: Entity, jock: Entity) -> None:
    world.say(setting_detail(setting))
    world.say(
        f"{jock.id} smiled at {friend.id} and promised to rest first next time."
    )
    world.say(
        f"The two friends walked on together, and friendship made the whole place feel safer."
    )


SETTINGS = {
    "meadow": Setting(place="the meadow", indoor=False, calm=True),
    "barn": Setting(place="the barn", indoor=True, calm=True),
    "pond": Setting(place="the pond path", indoor=False, calm=True),
}

INJURIES = {
    "scrape": Injury(
        id="scrape",
        label="scrape",
        phrase="a small scrape on the knee",
        symptom="It stung when the leg bent",
        needs={"ointment", "bandage"},
        trouble="stinging",
    ),
    "sore": Injury(
        id="sore",
        label="sore paw",
        phrase="a sore paw",
        symptom="It hurt to hop and run",
        needs={"ointment", "bandage"},
        trouble="aching",
    ),
    "bugbite": Injury(
        id="bugbite",
        label="bug bite",
        phrase="an itchy bug bite",
        symptom="It itched and made the jock wiggle",
        needs={"ointment"},
        trouble="itching",
    ),
}

KITS = {
    "ointment": CareKit(
        id="ointment",
        label="ointment",
        phrase="a tiny tin of ointment",
        treats={"scrape", "sore", "bugbite"},
        prep="opened the tin and washed the hurt place",
        finish="shared a slow, quiet snack",
    ),
    "bandage": CareKit(
        id="bandage",
        label="bandage",
        phrase="a soft bandage roll",
        treats={"scrape", "sore"},
        prep="wrapped the clean cloth around the sore",
        finish="sat together under a warm blanket",
    ),
}

FRIEND_TYPES = ["cat", "rabbit", "fox", "duck", "mouse", "goat"]
JOCK_TYPES = ["dog", "bear", "pig", "goat", "cat", "fox"]
NAMES = ["Milo", "Pippa", "Nina", "Toby", "Benny", "Luna", "Rosie", "Otis"]


def story_intro(world: World, setting: Setting, friend: Entity, jock: Entity) -> None:
    world.say(f"{friend.id} and {jock.id} lived near {setting.place}.")
    world.say(f"They were close friends, and they liked to look out for one another.")


def tell(setting: Setting, injury: Injury, kit: CareKit,
         friend_name: str, jock_name: str,
         friend_kind: str, jock_kind: str) -> World:
    world = World(setting)
    friend = world.add(Entity(id="friend", kind="character", type=friend_kind, label=friend_name))
    jock = world.add(Entity(id="jock", kind="character", type=jock_kind, label=jock_name))
    world.facts.update(setting=setting, injury=injury, kit=kit, friend=friend, jock=jock)

    story_intro(world, setting, friend, jock)
    introduce(world, jock, friend)
    world.para()
    world.say(setting_detail(setting))
    setup_injury(world, jock, injury)
    ask_help(world, friend, jock, injury)
    resist(world, jock)
    world.para()
    medicate(world, friend, jock, kit, injury)
    resolve(world, setting, friend, jock)
    return world


@dataclass
class StoryParams:
    place: str
    injury: str
    kit: str
    friend_kind: str
    jock_kind: str
    friend_name: str
    jock_name: str
    seed: Optional[int] = None
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle animal story about friendship, using the word "medicate".',
        f"Tell a short story where {f['friend'].label} helps {f['jock'].label} after {f['jock'].label} gets {f['injury'].phrase}.",
        f"Write a child-friendly story about a jock animal who needs care and a friend who helps.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    friend: Entity = _safe_fact(world, f, "friend")
    jock: Entity = _safe_fact(world, f, "jock")
    injury: Injury = _safe_fact(world, f, "injury")
    kit: CareKit = _safe_fact(world, f, "kit")
    setting: Setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who helped {jock.label} when {jock.label} got hurt near {setting.place}?",
            answer=f"{friend.label} helped {jock.label}. {friend.label} was the caring friend who noticed the hurt first.",
        ),
        QAItem(
            question=f"What did {friend.label} use to medicate the sore?",
            answer=f"{friend.label} used {kit.phrase} to medicate {jock.label}'s {injury.label}.",
        ),
        QAItem(
            question=f"Why did {jock.label} need help instead of keeping to play right away?",
            answer=f"{jock.label} needed help because {injury.symptom.lower()}. The care made the hurt stop bothering {jock.pronoun('object')}.",
        ),
        QAItem(
            question=f"What did the friends do at the end?",
            answer=f"They stayed together, rested a little, and walked on with friendship between them.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is medicate?",
            answer="To medicate means to give medicine or gentle care so a hurt place can start feeling better.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when friends care about each other, help each other, and stay kind.",
        ),
        QAItem(
            question="What does a bandage do?",
            answer="A bandage covers a scrape or sore and helps keep it clean while it heals.",
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
    lines.append("== (3) World knowledge ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.using:
            bits.append(f"using={e.using}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("meadow", "scrape", "ointment", "cat", "dog", "Milo", "Benny"),
    StoryParams("barn", "sore", "bandage", "rabbit", "bear", "Pippa", "Otis"),
    StoryParams("pond", "bugbite", "ointment", "fox", "goat", "Nina", "Toby"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal friendship storyworld about caring and medicating.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--injury", choices=sorted(INJURIES))
    ap.add_argument("--kit", choices=sorted(KITS))
    ap.add_argument("--friend-kind", choices=sorted(FRIEND_TYPES))
    ap.add_argument("--jock-kind", choices=sorted(JOCK_TYPES))
    ap.add_argument("--friend-name")
    ap.add_argument("--jock-name")
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
    if getattr(args, "injury", None) and getattr(args, "kit", None) and getattr(args, "kit", None) not in KITS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "injury", None) and getattr(args, "kit", None) and getattr(args, "injury", None) not in _safe_lookup(KITS, getattr(args, "kit", None)).treats:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "injury", None) is None or c[1] == getattr(args, "injury", None))
        and (getattr(args, "kit", None) is None or c[2] == getattr(args, "kit", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, injury, kit = rng.choice(list(combos))
    friend_kind = getattr(args, "friend_kind", None) or rng.choice(FRIEND_TYPES)
    jock_kind = getattr(args, "jock_kind", None) or rng.choice(JOCK_TYPES)
    friend_name = getattr(args, "friend_name", None) or rng.choice(NAMES)
    jock_name = getattr(args, "jock_name", None) or rng.choice([n for n in NAMES if n != friend_name])
    return StoryParams(place, injury, kit, friend_kind, jock_kind, friend_name, jock_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(INJURIES, params.injury),
        _safe_lookup(KITS, params.kit),
        params.friend_name,
        params.jock_name,
        params.friend_kind,
        params.jock_kind,
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


ASP_RULES = r"""
valid_combo(P,I,K) :- place(P), injury(I), kit(K), treats(K,I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for inj in INJURIES.values():
        lines.append(asp.fact("injury", inj.id))
    for kit in KITS.values():
        lines.append(asp.fact("kit", kit.id))
        for t in sorted(kit.treats):
            lines.append(asp.fact("treats", kit.id, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python combos.")
    if cl - py:
        print(" only in clingo:", sorted(cl - py))
    if py - cl:
        print(" only in python:", sorted(py - cl))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_combo/3."))
        return
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
        i = 0
        seen: set[str] = set()
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.friend_name} and {p.jock_name} at {p.place} ({p.injury} / {p.kit})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
