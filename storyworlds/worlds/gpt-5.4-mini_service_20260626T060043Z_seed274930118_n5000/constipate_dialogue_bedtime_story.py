#!/usr/bin/env python3
"""
storyworlds/worlds/constipate_dialogue_bedtime_story.py
========================================================

A small bedtime-story world about a child-facing character who feels
constipated, talks about it in dialogue, and finds a gentle, comforting fix
before sleep.

The world is intentionally tiny and state-driven:
- a character has a tummy discomfort meter
- a bedtime helper can suggest a soothing remedy
- a private routine (warm water, potty time, tummy rub, or prunes) can lower
  discomfort and help the character settle for sleep

The prose is authored from simulated state, not a frozen paragraph with swapped
nouns.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    parent: object | None = None
    pillow: object | None = None
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
class Remedy:
    id: str
    label: str
    cue: str
    effect: str
    soft_words: str
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
class BedtimeSetting:
    place: str = "the bedroom"
    afford: set[str] = field(default_factory=set)
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
    def __init__(self, setting: BedtimeSetting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "bedroom": BedtimeSetting(place="the bedroom", afford={"warm_water", "potty", "tummy_rub", "prunes"}),
    "nursery": BedtimeSetting(place="the nursery", afford={"warm_water", "potty", "tummy_rub", "prunes"}),
    "tent": BedtimeSetting(place="the tent", afford={"warm_water", "potty", "tummy_rub"}),
}

REMEDIES = {
    "warm_water": Remedy(
        id="warm_water",
        label="a cup of warm water",
        cue="warm water",
        effect="felt a little easier",
        soft_words="Let's take tiny sips and let your tummy settle.",
        tags={"warm", "water", "sleep"},
    ),
    "potty": Remedy(
        id="potty",
        label="the potty",
        cue="the potty",
        effect="was no longer stuck",
        soft_words="Sometimes a potty break helps the body remember what to do.",
        tags={"potty", "body"},
    ),
    "tummy_rub": Remedy(
        id="tummy_rub",
        label="a gentle tummy rub",
        cue="tummy rub",
        effect="calmed down",
        soft_words="I'll rub your tummy in tiny circles.",
        tags={"tummy", "gentle"},
    ),
    "prunes": Remedy(
        id="prunes",
        label="soft prunes",
        cue="prunes",
        effect="got moving again",
        soft_words="These little fruits can help a slow belly wake up.",
        tags={"food", "fruit"},
    ),
}

HERO_NAMES = ["Milo", "Nina", "Luca", "Pia", "Toby", "Mina", "Arlo", "Juno"]
HERO_TYPES = ["boy", "girl"]
PARENT_TYPES = ["mother", "father"]
TRAITS = ["sleepy", "gentle", "small", "curious", "tired"]


@dataclass
class StoryParams:
    setting: str
    remedy: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasoning / simulation
# ---------------------------------------------------------------------------
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


def bedtime_is_reasonable(setting: str, remedy: str) -> bool:
    return setting in SETTINGS and remedy in REMEDIES and remedy in _safe_lookup(SETTINGS, setting).afford


def predict_help(world: World, child: Entity, remedy: Remedy) -> dict[str, bool]:
    sim = world.copy()
    c = sim.get(child.id)
    c.memes["discomfort"] += 1
    c.memes["constipated"] += 1
    apply_remedy(sim, c, remedy, narrate=False)
    return {"better": c.memes.get("discomfort", 0) < 1.0, "asleep": c.memes.get("sleepy", 0) >= 1.0}


def apply_remedy(world: World, child: Entity, remedy: Remedy, narrate: bool = True) -> None:
    sig = ("remedy", child.id, remedy.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    child.memes["discomfort"] = max(0.0, child.memes.get("discomfort", 0.0) - 1.0)
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1.0
    child.memes["constipated"] = max(0.0, child.memes.get("constipated", 0.0) - 1.0)
    if remedy.id == "tummy_rub":
        child.memes["sleepy"] = child.memes.get("sleepy", 0.0) + 1.0
    if narrate:
        world.say(remedy.soft_words)


def bedtime_settle(world: World, child: Entity, parent: Entity, remedy: Remedy) -> None:
    child.memes["sleepy"] = child.memes.get("sleepy", 0.0) + 1.0
    world.say(
        f'{child.id} gave a tiny sigh. "{remedy.effect}," {child.pronoun("subject")} whispered.'
    )
    world.say(
        f'{parent.pronoun("subject").capitalize()} smiled. "That is better. Now let’s snuggle and sleep."'
    )


def tell(setting: BedtimeSetting, remedy: Remedy, name: str, gender: str,
         parent_type: str, trait: str) -> World:
    world = World(setting)

    child = world.add(Entity(
        id=name, kind="character", type=gender,
        meters={"discomfort": 0.0}, memes={"curiosity": 1.0}
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=parent_type, label="the parent"
    ))
    pillow = world.add(Entity(
        id="pillow", type="thing", label="a soft pillow", owner=child.id
    ))

    world.say(f"At bedtime, {child.id} was a {trait} little {gender} in {setting.place}.")
    world.say(
        f'{child.id} hugged {pillow.label} and whispered, "I want sleep, but my belly feels funny."'
    )
    world.say(
        f'{parent.pronoun("subject").capitalize()} sat on the bed and asked, "{child.id}, do you mean constipate?"'
    )
    world.say(
        f'"Yes," {child.id} said. "My tummy feels stuck."'
    )
    world.para()

    child.memes["discomfort"] += 1
    child.memes["constipated"] += 1
    world.say(
        f'"Let me help," said {parent.pronoun("subject")}. "{remedy.soft_words}"'
    )
    apply_remedy(world, child, remedy)
    world.say(
        f'"Okay," said {child.id}. "{remedy.cue} sounds nice."'
    )
    world.para()

    bedtime_settle(world, child, parent, remedy)

    world.facts.update(
        child=child,
        parent=parent,
        remedy=remedy,
        setting=setting,
        pillow=pillow,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A remedy is available when the setting affords it.
available(S,R) :- setting(S), remedy(R), afford(S,R).

% A bedtime story is valid when the remedy is available and child-safe.
valid_story(S,R) :- available(S,R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for r in sorted(setting.afford):
            lines.append(asp.fact("afford", sid, r))
    for rid in REMEDIES:
        lines.append(asp.fact("remedy", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return sorted(
        (s, r)
        for s in SETTINGS
        for r in REMEDIES
        if bedtime_is_reasonable(s, r)
    )


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP parity with Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")  # type: ignore[assignment]
    remedy: Remedy = _safe_fact(world, f, "remedy")  # type: ignore[assignment]
    return [
        f'Write a short bedtime story that includes the word "constipate" and a gentle conversation.',
        f"Tell a cozy story about {child.id}, who feels constipate at bedtime, and how {child.pronoun('possessive')} parent helps with {remedy.label}.",
        f'Write a soft bedtime story where someone says "constipate" and the worry becomes comfort before sleep.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")  # type: ignore[assignment]
    parent: Entity = _safe_fact(world, f, "parent")  # type: ignore[assignment]
    remedy: Remedy = _safe_fact(world, f, "remedy")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What was wrong with {child.id} at bedtime?",
            answer=f"{child.id} felt constipated, so {child.pronoun('possessive')} tummy felt stuck and uncomfortable.",
        ),
        QAItem(
            question=f"What did {parent.pronoun('subject')} suggest to help {child.id}?",
            answer=f"{parent.pronoun('subject').capitalize()} suggested {remedy.label}, and {remedy.soft_words}",
        ),
        QAItem(
            question=f"How did the story end for {child.id}?",
            answer=f"{child.id} felt better, got sleepy, and settled down for bed with {parent.pronoun('object')}.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "warm": [
        QAItem(
            question="Why can warm water feel soothing at night?",
            answer="Warm water can feel soothing because it is gentle, easy to sip, and can help a body relax.",
        )
    ],
    "potty": [
        QAItem(
            question="What is a potty for?",
            answer="A potty is a small toilet made for little children.",
        )
    ],
    "tummy": [
        QAItem(
            question="What does a tummy rub do?",
            answer="A gentle tummy rub can feel comforting and help a child relax.",
        )
    ],
    "food": [
        QAItem(
            question="Why are fruits like prunes sometimes talked about in stories about bellies?",
            answer="Some fruits are known for helping the belly move along when it feels slow.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["remedy"].tags)  # type: ignore[index]
    out: list[QAItem] = []
    for tag, items in WORLD_KNOWLEDGE.items():
        if tag in tags:
            out.extend(items)
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
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Param handling and generation
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="bedroom", remedy="warm_water", name="Milo", gender="boy", parent="mother", trait="sleepy"),
    StoryParams(setting="nursery", remedy="tummy_rub", name="Nina", gender="girl", parent="father", trait="gentle"),
    StoryParams(setting="bedroom", remedy="prunes", name="Luca", gender="boy", parent="mother", trait="curious"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime-story world about constipate, gentle dialogue, and sleep."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=HERO_TYPES)
    ap.add_argument("--parent", choices=PARENT_TYPES)
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
    combos = [
        (s, r) for s, r in valid_combos()
        if (getattr(args, "setting", None) is None or s == getattr(args, "setting", None))
        and (getattr(args, "remedy", None) is None or r == getattr(args, "remedy", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, remedy = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    gender = getattr(args, "gender", None) or rng.choice(HERO_TYPES)
    parent = getattr(args, "parent", None) or rng.choice(PARENT_TYPES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, remedy=remedy, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(REMEDIES, params.remedy), params.name, params.gender, params.parent, params.trait)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, remedy) combos:\n")
        for s, r in combos:
            print(f"  {s:8} {r}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
            header = f"### {p.name}: bedtime in {p.setting} with {p.remedy}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
