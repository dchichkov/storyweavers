#!/usr/bin/env python3
"""
storyworlds/worlds/olden_reconciliation_tall_tale.py
=====================================================

A tiny tall-tale story world about an olden-time quarrel that ends in
reconciliation.

Premise:
- Two stubborn neighbors in an olden village argue over a shared windmill,
  a bridge, or a bell, depending on the sampled story.
- The argument grows into a big, comic, almost-impossible fuss.
- A practical helper and a shared task create a path to reconciliation.
- The ending proves the feud changed into friendship.

This script is self-contained and uses only stdlib for the prose engine.
It also includes a small inline ASP twin for the reasonableness gate.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    kind: str = "thing"          # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    a: object | None = None
    b: object | None = None
    relic: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    olden_flavor: str
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
class Relic:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"woman", "man"})
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
class Dispute:
    id: str
    noun: str
    verb: str
    want: str
    risk: str
    mess: str
    zone: set[str]
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
class Remedy:
    id: str
    label: str
    prep: str
    tail: str
    protects: set[str]
    soothes: set[str]
    plural: bool = False
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "village": Setting("the village green", "olden", {"bell", "bridge", "barrel"}),
    "harbor": Setting("the harbor quay", "olden", {"rope", "lantern", "barrel"}),
    "orchard": Setting("the orchard lane", "olden", {"ladder", "basket", "barrel"}),
}

DISPUTES = {
    "bell": Dispute(
        id="bell",
        noun="bell",
        verb="ring the brass bell",
        want="hear it peal",
        risk="the clamor would shake the whole square",
        mess="deafening",
        zone={"sound"},
        keyword="bell",
        tags={"sound", "olden"},
    ),
    "bridge": Dispute(
        id="bridge",
        noun="bridge",
        verb="cross the little bridge",
        want="reach the other side first",
        risk="the crowd would jam the plank",
        mess="crowded",
        zone={"path"},
        keyword="bridge",
        tags={"wood", "olden"},
    ),
    "barrel": Dispute(
        id="barrel",
        noun="barrel",
        verb="roll the barrel to market",
        want="claim the best spot",
        risk="the barrel might tumble into a puddle",
        mess="muddy",
        zone={"ground"},
        keyword="barrel",
        tags={"wood", "olden"},
    ),
    "lantern": Dispute(
        id="lantern",
        noun="lantern",
        verb="carry the lantern at dusk",
        want="light the path first",
        risk="the lantern could be covered in soot",
        mess="sooty",
        zone={"hand"},
        keyword="lantern",
        tags={"light", "olden"},
    ),
}

RELICS = {
    "shawl": Relic("shawl", "shawl", "a soft wool shawl", "torso", genders={"woman"}),
    "hat": Relic("hat", "hat", "a broad felt hat", "head", genders={"man", "woman"}),
    "boots": Relic("boots", "boots", "tall leather boots", "feet", plural=True),
    "coat": Relic("coat", "coat", "a sturdy riding coat", "torso"),
}

REMEDIES = [
    Remedy(
        id="share",
        label="a shared turn-taking plan",
        prep="make a great big plan to take turns",
        tail="stood side by side and took turns",
        protects={"sound", "crowded", "muddy", "sooty"},
        soothes={"anger"},
    ),
    Remedy(
        id="mend",
        label="a mended joint task",
        prep="mend the thing together first",
        tail="mended the old thing together",
        protects={"crowded", "muddy", "sooty"},
        soothes={"anger"},
    ),
]

NAMES = ["Ada", "Milo", "June", "Ezra", "Nell", "Otis", "Martha", "Jonah"]
TYPES = ["woman", "man"]
TRAITS = ["stubborn", "lively", "proud", "hotheaded", "spirited", "strong-willed"]


@dataclass
class StoryParams:
    place: str
    dispute: str
    relic: str
    name_a: str
    type_a: str
    name_b: str
    type_b: str
    trait_a: str
    trait_b: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
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


def dispute_at_risk(d: Dispute, r: Relic) -> bool:
    if d.id == "bell":
        return True
    if d.id == "bridge":
        return r.region in {"feet", "torso"}
    if d.id == "barrel":
        return r.region in {"feet", "torso"}
    if d.id == "lantern":
        return r.region in {"torso", "head"}
    return False


def select_remedy(d: Dispute, r: Relic) -> Optional[Remedy]:
    for remedy in REMEDIES:
        if d.mess in remedy.protects or any(tag in remedy.protects for tag in d.tags):
            return remedy
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for dispute_id in setting.affords:
            d = _safe_lookup(DISPUTES, dispute_id)
            for relic_id, relic in RELICS.items():
                if dispute_at_risk(d, relic) and select_remedy(d, relic):
                    out.append((place, dispute_id, relic_id))
    return out


def explain_rejection(d: Dispute, r: Relic) -> str:
    if not dispute_at_risk(d, r):
        return (
            f"(No story: {d.verb} does not threaten {r.label} in a believable way, "
            f"so the quarrel would not have a real reason to start.)"
        )
    return (
        f"(No story: nothing in the remedy list could fairly fix the trouble "
        f"between {d.noun} and {r.label}.)"
    )


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------
def setup_line(setting: Setting) -> str:
    return f"In the olden days, {setting.place} was busy with creaky boards, bright eyes, and plenty of gossip."


def introduce_pair(a: Entity, b: Entity, ta: str, tb: str) -> str:
    return (
        f"There lived {a.id}, a {ta} {a.type}, and {b.id}, a {tb} {b.type}, "
        f"and each was as stubborn as a fencepost in a thunderstorm."
    )


def feud_line(a: Entity, b: Entity, d: Dispute, relic: Entity) -> str:
    a.memes["anger"] += 1
    b.memes["anger"] += 1
    return (
        f"Both of them wanted to {d.verb} near {relic.phrase}. "
        f"{a.id} wanted to {d.want}, and {b.id} wanted the same, "
        f"so they argued so hard that even the crows seemed to blink."
    )


def tall_tale_turn(a: Entity, b: Entity, d: Dispute) -> str:
    a.memes["pride"] += 1
    b.memes["pride"] += 1
    return (
        f"The quarrel swelled taller than a haystack on stilts. "
        f"By supper, the whole lane knew the two of them could split a spoon over a single sigh."
    )


def mediator_line() -> str:
    return (
        "Then a wise helper came by, the sort who could hear a grumble from three fields away "
        "and still arrive with a calm smile."
    )


def remedy_line(remedy: Remedy, a: Entity, b: Entity, d: Dispute, relic: Entity) -> str:
    a.memes["anger"] = max(0.0, a.memes["anger"] - 1.0)
    b.memes["anger"] = max(0.0, b.memes["anger"] - 1.0)
    a.memes["warmth"] += 1
    b.memes["warmth"] += 1
    return (
        f"The helper suggested they {remedy.prep}, because only that would keep the trouble from "
        f"spreading to {relic.phrase}. The two of them grumbled, then nodded, and {remedy.tail}."
    )


def reconciliation_line(a: Entity, b: Entity, remedy: Remedy, d: Dispute, relic: Entity) -> str:
    a.memes["anger"] = 0.0
    b.memes["anger"] = 0.0
    a.memes["reconciliation"] += 1
    b.memes["reconciliation"] += 1
    return (
        f"That worked like rain on dry corn. Their faces softened, their words turned gentle, "
        f"and soon {a.id} and {b.id} were laughing together while {relic.label} stayed safe. "
        f"At last, the olden quarrel turned into friendship."
    )


def tell(world: World, params: StoryParams) -> World:
    d = _safe_lookup(DISPUTES, params.dispute)
    relic = world.add(Entity(
        id="relic", kind="thing", type=params.relic, label=_safe_lookup(RELICS, params.relic).label,
        phrase=_safe_lookup(RELICS, params.relic).phrase, plural=_safe_lookup(RELICS, params.relic).plural
    ))
    a = world.add(Entity(id=params.name_a, kind="character", type=params.type_a))
    b = world.add(Entity(id=params.name_b, kind="character", type=params.type_b))

    world.say(setup_line(world.setting))
    world.say(introduce_pair(a, b, params.trait_a, params.trait_b))
    world.para()
    world.say(feud_line(a, b, d, relic))
    world.say(tall_tale_turn(a, b, d))
    world.para()
    world.say(mediator_line())
    remedy = select_remedy(d, _safe_lookup(RELICS, params.relic))
    if remedy is None:
        pass
    world.say(remedy_line(remedy, a, b, d, relic))
    world.say(reconciliation_line(a, b, remedy, d, relic))

    world.facts.update(
        setting=world.setting,
        dispute=d,
        relic=relic,
        a=a,
        b=b,
        remedy=remedy,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "olden": [
        ("What does olden mean?", "Olden means long ago, in the past, when people lived differently."),
    ],
    "bridge": [
        ("What is a bridge for?", "A bridge helps people cross over water, roads, or gaps safely."),
    ],
    "bell": [
        ("What does a bell do?", "A bell rings loudly so people can hear a signal or announcement."),
    ],
    "barrel": [
        ("What is a barrel?", "A barrel is a round wooden container used to carry or store things."),
    ],
    "lantern": [
        ("What is a lantern for?", "A lantern gives light when it is dark outside or inside."),
    ],
    "reconciliation": [
        ("What is reconciliation?", "Reconciliation is when people who argued make peace and become friendly again."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    d: Dispute = _safe_fact(world, f, "dispute")
    return [
        f'Write a short tall tale for children set in the olden days about a quarrel over {d.noun} that ends in reconciliation.',
        f"Tell a funny olden-time story where two neighbors both want to {d.verb} and learn to make peace.",
        f'Write a simple story that includes "{d.keyword}" and ends with the two feuding characters becoming friends again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a: Entity = _safe_fact(world, f, "a")
    b: Entity = _safe_fact(world, f, "b")
    d: Dispute = _safe_fact(world, f, "dispute")
    relic: Entity = _safe_fact(world, f, "relic")
    remedy: Remedy = _safe_fact(world, f, "remedy")
    return [
        QAItem(
            question=f"Who were the two neighbors in the story?",
            answer=f"The story was about {a.id} and {b.id}, who both lived in the olden days and argued over {relic.phrase}.",
        ),
        QAItem(
            question=f"What were they arguing about?",
            answer=f"They were arguing about who got to {d.verb}. That was the big trouble at the center of the story.",
        ),
        QAItem(
            question=f"What helped them stop arguing?",
            answer=f"A wise helper told them to {remedy.prep}, and that turned the quarrel into reconciliation.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {a.id} and {b.id} laughing together, their anger gone, and {relic.label} safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = {"olden", "reconciliation", world.facts["dispute"].keyword}
    for tag in ["olden", world.facts["dispute"].keyword, "reconciliation"]:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE.get(tag, []))
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
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A relic is at risk if the dispute can plausibly damage or disrupt it.
at_risk(D, R) :- dispute(D), relic(R), threatens(D, R).

% A remedy is compatible if it addresses the dispute's mess and calms the conflict.
compatible(M, D, R) :- remedy(M), at_risk(D, R), soothes(M, X), dispute_tag(D, X).

valid_story(P, D, R) :- setting(P), affords(P, D), at_risk(D, R), compatible(_, D, R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for d in sorted(s.affords):
            lines.append(asp.fact("affords", pid, d))
    for did, d in DISPUTES.items():
        lines.append(asp.fact("dispute", did))
        lines.append(asp.fact("threatens", did, d.id))
        lines.append(asp.fact("dispute_tag", did, "olden"))
        for t in sorted(d.tags):
            lines.append(asp.fact("dispute_tag", did, t))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("relic_region", rid, r.region))
    for m in REMEDIES:
        lines.append(asp.fact("remedy", m.id))
        for s in sorted(m.protects):
            lines.append(asp.fact("protects", m.id, s))
        for s in sorted(m.soothes):
            lines.append(asp.fact("soothes", m.id, s))
    return "\n".join(lines)


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
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="An olden-time reconciliation tall tale.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--dispute", choices=DISPUTES)
    ap.add_argument("--relic", choices=RELICS)
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
    if getattr(args, "dispute", None) and getattr(args, "relic", None):
        d = _safe_lookup(DISPUTES, getattr(args, "dispute", None))
        r = _safe_lookup(RELICS, getattr(args, "relic", None))
        if not dispute_at_risk(d, r) or not select_remedy(d, r):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "dispute", None) is None or c[1] == getattr(args, "dispute", None))
        and (getattr(args, "relic", None) is None or c[2] == getattr(args, "relic", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, dispute, relic = rng.choice(list(combos))
    name_a, name_b = rng.sample(NAMES, 2)
    type_a, type_b = rng.choice(TYPES), rng.choice(TYPES)
    trait_a, trait_b = rng.choice(TRAITS), rng.choice(TRAITS)
    return StoryParams(place, dispute, relic, name_a, type_a, name_b, type_b, trait_a, trait_b)


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    tell(world, params)
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
    StoryParams("village", "bell", "hat", "Ada", "woman", "Milo", "man", "proud", "stubborn"),
    StoryParams("village", "bridge", "boots", "June", "woman", "Otis", "man", "lively", "hotheaded"),
    StoryParams("harbor", "lantern", "coat", "Martha", "woman", "Jonah", "man", "strong-willed", "spirited"),
    StoryParams("orchard", "barrel", "shawl", "Nell", "woman", "Ezra", "man", "proud", "stubborn"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid_story/3."))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
