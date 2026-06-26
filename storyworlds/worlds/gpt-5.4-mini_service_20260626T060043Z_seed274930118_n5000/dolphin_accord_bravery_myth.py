#!/usr/bin/env python3
"""
storyworlds/worlds/dolphin_accord_bravery_myth.py
==================================================

A standalone story world for a small mythic sea tale: a child or young sailor
meets a dolphin, faces a test of bravery, and reaches an accord that changes
the ending image.

The world is intentionally compact and constraint-checked:
- one setting, one central task, one danger, one meaningful accord
- stateful meters and memes drive the prose
- the story reads like a myth, but stays concrete and child-facing
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    prize: object | None = None
    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "daughter", "maid"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "son", "boy-hero"}:
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Setting:
    place: str = "the blue cove"
    sea_state: str = "calm"
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
class Task:
    id: str
    verb: str
    gerund: str
    risk: str
    danger: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Accord:
    id: str
    label: str
    promise: str
    tale_line: str
    guards: set[str] = field(default_factory=set)
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class StoryParams:
    setting: str
    task: str
    prize: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "cove": Setting(place="the blue cove", sea_state="calm", affords={"swim", "dive"}),
    "reef": Setting(place="the bright reef", sea_state="calm", affords={"swim", "dive"}),
    "harbor": Setting(place="the harbor mouth", sea_state="tide-turning", affords={"swim", "dive"}),
    "isle": Setting(place="the island shallows", sea_state="tide-turning", affords={"swim", "dive"}),
}

TASKS = {
    "swim": Task(
        id="swim",
        verb="swim to the reef",
        gerund="swimming through the water",
        risk="deep water",
        danger="the current could pull the little boat away",
        keyword="dolphin",
        tags={"sea", "dolphin", "water"},
    ),
    "dive": Task(
        id="dive",
        verb="dive for the moon-pearl",
        gerund="diving under the waves",
        risk="the dark water below",
        danger="the cave mouth could swallow a careless swimmer",
        keyword="accord",
        tags={"sea", "dolphin", "pearl"},
    ),
}

PRIZES = {
    "shell": Prize(id="shell", label="shell", phrase="a bright shell charm", region="neck"),
    "net": Prize(id="net", label="net", phrase="a small fisher net", region="hands", plural=False),
    "cloak": Prize(id="cloak", label="cloak", phrase="a red wool cloak", region="back"),
}

ACCORDS = {
    "breath": Accord(
        id="breath",
        label="a breath-held accord",
        promise="to wait for the dolphin's signal before moving",
        tale_line="the dolphin rose first, and the child followed when the sea was safe",
        guards={"deep water", "dark water below"},
    ),
    "lantern": Accord(
        id="lantern",
        label="a lantern accord",
        promise="to carry a small lantern and stay near the shining path",
        tale_line="the lantern marked the way between the rocks",
        guards={"dark water below"},
    ),
}

HERO_NAMES = ["Ari", "Mina", "Taro", "Lina", "Pere", "Sora", "Kai", "Nina"]
HELPER_NAMES = ["Neri", "Mako", "Piko", "Runa", "Daro"]
HERO_TYPES = ["boy", "girl"]
HELPER_TYPES = ["dolphin"]

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(T, P) :- risk_of(T, R), worn_on(P, R).
compatible(A, T, P) :- task(T), prize_at_risk(T, P),
                       task_danger(T, D), accord(A),
                       guards(A, D).
valid_story(S, T, P, A) :- setting(S), task(T), prize(P), accord(A),
                           affords(S, T), compatible(A, T, P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", sid, t))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("risk_of", tid, t.risk))
        lines.append(asp.fact("task_danger", tid, t.danger))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for aid, a in ACCORDS.items():
        lines.append(asp.fact("accord", aid))
        for g in sorted(a.guards):
            lines.append(asp.fact("guards", aid, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    python_set = set(valid_combos(with_accord=True))
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------
def prize_at_risk(task: Task, prize: Prize) -> bool:
    return prize.region in {"neck", "hands", "back"} or task.id == "dive"


def select_accord(task: Task, prize: Prize) -> Optional[Accord]:
    for accord in ACCORDS.values():
        if task.danger in accord.guards:
            return accord
    return None


def valid_combos(with_accord: bool = False) -> list[tuple]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid in setting.affords:
            task = _safe_lookup(TASKS, tid)
            for pid, prize in PRIZES.items():
                if not prize_at_risk(task, prize):
                    continue
                accord = select_accord(task, prize)
                if accord is None:
                    continue
                if with_accord:
                    combos.append((sid, tid, pid, accord.id))
                else:
                    combos.append((sid, tid, pid))
    return combos


def explain_rejection(task: Task, prize: Prize) -> str:
    return (
        f"(No story: {task.gerund} does not create a believable danger for the {prize.label}, "
        f"or no accord in this world truly answers that danger.)"
    )


# ---------------------------------------------------------------------------
# Narration
# ---------------------------------------------------------------------------
def intro(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"{hero.id} was a young {hero.type} who listened to the sea as if it were telling an old myth."
    )
    world.say(
        f"One bright dawn, {hero.id} met {helper.id}, a dolphin with a silver back and a quick, curious eye."
    )


def desire(world: World, hero: Entity, task: Task) -> None:
    hero.memes["wonder"] = hero.memes.get("wonder", 0) + 1
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    world.say(
        f"{hero.id} wanted to {task.verb}, because {task.gerund} felt like chasing a story the waves had hidden."
    )


def gift_and_warning(world: World, helper: Entity, prize: Entity, task: Task) -> None:
    prize.meters["shining"] = 1
    world.say(
        f"{helper.id} circled once around the water and nudged up {prize.phrase} from the sand."
    )
    world.say(
        f"But the dolphin's bright eyes looked toward {task.danger}, as if to warn that courage would be needed."
    )


def fear(world: World, hero: Entity, task: Task) -> None:
    hero.memes["fear"] = hero.memes.get("fear", 0) + 1
    world.say(
        f"{hero.id}'s knees felt small, and {hero.pronoun('possessive')} heart beat hard against the hush of the tide."
    )
    world.say(
        f"{hero.id} knew the sea could be kind, but it could also hide {task.danger}."
    )


def accord_offer(world: World, hero: Entity, helper: Entity, task: Task, prize: Entity) -> Accord:
    accord = select_accord(task, prize)
    if accord is None:
        _fallback_pool = globals().get("ACCORDS") or globals().get("ACCORDES") or []
        if hasattr(_fallback_pool, "values"):
            _fallback_pool = list(_fallback_pool.values())
        accord = next(iter(_fallback_pool), None)
        if accord is None:
            raise StoryError
    world.facts["accord"] = accord
    world.say(
        f"Then {helper.id} rose beside the moonlit foam and made an accord with {hero.id}: {accord.promise}."
    )
    return accord


def brave_choice(world: World, hero: Entity, task: Task, accord: Accord) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    hero.meters["resolve"] = hero.meters.get("resolve", 0) + 1
    world.zone = {task.danger}
    world.say(
        f"{hero.id} took one brave breath and followed the sign. That was the moment {hero.id} chose courage over hurry."
    )


def resolution(world: World, hero: Entity, helper: Entity, prize: Entity, task: Task, accord: Accord) -> None:
    hero.memes["fear"] = 0
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    prize.meters["safe"] = 1
    world.say(
        f"The accord held: {accord.tale_line}."
    )
    world.say(
        f"At last, {hero.id} came back smiling with {prize.phrase}, and {helper.id} leaped beside {hero.pronoun('object')} like a guardian from a sea-song."
    )


def tell(setting: Setting, task: Task, prize_cfg: Prize, hero_name: str, hero_type: str,
         helper_name: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, label="the dolphin"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.id,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
    ))

    intro(world, hero, helper)
    world.para()
    desire(world, hero, task)
    gift_and_warning(world, helper, prize, task)
    fear(world, hero, task)
    world.para()
    accord = accord_offer(world, hero, helper, task, prize)
    brave_choice(world, hero, task, accord)
    resolution(world, hero, helper, prize, task, accord)

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        task=task,
        setting=setting,
        accord=accord,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    task = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "task")
    return [
        f'Write a short mythic story for a young child about a dolphin and an accord, and include the word "dolphin".',
        f"Tell a gentle sea myth where {hero.id} learns bravery from a dolphin while trying to {task.verb}.",
        f"Write a small story in a myth style where the sea offers a test, an accord, and a brave ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    prize = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prize")
    task = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "task")
    accord = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "accord")
    return [
        QAItem(
            question=f"Who is the story about, and who helps {hero.id} in the water?",
            answer=f"The story is about {hero.id}, and {helper.id} the dolphin helps with the sea task.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do in the story?",
            answer=f"{hero.id} wanted to {task.verb}.",
        ),
        QAItem(
            question=f"What made the story need bravery?",
            answer=f"The story needed bravery because {task.danger}.",
        ),
        QAItem(
            question=f"What accord did {hero.id} and the dolphin make?",
            answer=f"They made {accord.label}: {accord.promise}.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {hero.id} was brave enough to keep going, and {prize.phrase} came back safely.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "dolphin": [
        (
            "What is a dolphin?",
            "A dolphin is a sea mammal that breathes air, swims fast, and often lives in groups.",
        )
    ],
    "accord": [
        (
            "What is an accord?",
            "An accord is an agreement where two sides choose the same plan and keep to it.",
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery is doing something scary or hard even when you feel afraid.",
        )
    ],
    "myth": [
        (
            "What is a myth?",
            "A myth is an old story about important beings or events, often told to explain the world or teach a lesson.",
        )
    ],
    "sea": [
        (
            "Why do sailors watch the sea closely?",
            "Sailors watch the sea closely because wind, waves, and tides can change quickly and affect the trip.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "task").tags)
    tags.update({"dolphin", "accord", "bravery", "myth"})
    out: list[QAItem] = []
    for tag, items in WORLD_KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="cove", task="swim", prize="shell", hero_name="Ari", hero_type="boy", helper_name="Neri", helper_type="dolphin"),
    StoryParams(setting="reef", task="dive", prize="cloak", hero_name="Lina", hero_type="girl", helper_name="Mako", helper_type="dolphin"),
    StoryParams(setting="harbor", task="swim", prize="net", hero_name="Kai", hero_type="boy", helper_name="Runa", helper_type="dolphin"),
]


def valid_story_combos() -> list[tuple]:
    return valid_combos(with_accord=True)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic sea story world about a dolphin, an accord, and bravery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--gender", choices=["boy", "girl"])
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
    if getattr(args, "setting", None) and getattr(args, "task", None) and getattr(args, "prize", None):
        task = _safe_lookup(TASKS, getattr(args, "task", None))
        prize = _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not prize_at_risk(task, prize) or select_accord(task, prize) is None:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in valid_combos(with_accord=True)
        if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
        and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, task, prize, _accord = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(HERO_TYPES)
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice(HELPER_NAMES)
    return StoryParams(
        setting=setting,
        task=task,
        prize=prize,
        hero_name=hero_name,
        hero_type=gender,
        helper_name=helper_name,
        helper_type="dolphin",
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(TASKS, params.task),
        _safe_lookup(PRIZES, params.prize),
        params.hero_name,
        params.hero_type,
        params.helper_name,
        params.helper_type,
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for s in stories:
            print(" ", s)
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
            header = f"### {p.hero_name}: {p.task} at {p.setting} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
