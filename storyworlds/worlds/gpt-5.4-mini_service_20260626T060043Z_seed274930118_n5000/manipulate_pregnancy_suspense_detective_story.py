#!/usr/bin/env python3
"""
storyworlds/worlds/manipulate_pregnancy_suspense_detective_story.py
====================================================================

A small detective-style suspense world about a careful investigator, a hidden
pregnancy, and someone trying to manipulate the clues.

The seed premise is simple:
- A detective arrives to solve a quiet mystery.
- Someone has manipulated a few clues.
- The trail leads to a pregnancy secret.
- Suspense builds until the truth is uncovered and the tension clears.

The story stays close to classic detective-story style while keeping the world
small, concrete, and state-driven.
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
    role: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    detective: object | None = None
    pregnant: object | None = None
    suspect: object | None = None
    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.type

    def pronoun(self, case: str = "subject") -> str:
        gender_map = {
            "woman": {"subject": "she", "object": "her", "possessive": "her"},
            "man": {"subject": "he", "object": "him", "possessive": "his"},
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"},
        }
        return gender_map.get(self.type, {"subject": "it", "object": "it", "possessive": "its"})[case]
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
    place: str
    mood: str
    clues: list[str] = field(default_factory=list)
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
class Suspect:
    id: str
    label: str
    role: str
    truthfulness: str
    can_manipulate: bool = False
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


@dataclass
class StoryParams:
    place: str
    detective: str
    suspect: str
    clue: str
    pregnancy_secret: str
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
        self.trace_log: list[str] = []

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def join_list(items: list[str]) -> str:
    if len(items) <= 1:
        return items[0] if items else ""
    return ", ".join(items[:-1]) + ", and " + items[-1]


SETTINGS = {
    "station": Setting(place="the train station", mood="busy", clues=["ticket stub", "bench note", "coffee lid"]),
    "apartment": Setting(place="the apartment hallway", mood="quiet", clues=["door chain", "mail slot", "umbrella"]),
    "bakery": Setting(place="the corner bakery", mood="warm", clues=["receipt", "sugar packet", "tray cloth"]),
    "clinic": Setting(place="the small clinic lobby", mood="soft", clues=["clipboard", "tea cup", "window seat"]),
}

DETECTIVES = [
    ("Iris", "woman"),
    ("Nina", "woman"),
    ("Mara", "woman"),
    ("Eli", "man"),
    ("Jon", "man"),
]

SUSPECTS = [
    Suspect("neighbor", "the neighbor", "neighbor", "nervous", can_manipulate=True),
    Suspect("brother", "the brother", "brother", "protective", can_manipulate=True),
    Suspect("clerk", "the clerk", "clerk", "polite", can_manipulate=False),
    Suspect("friend", "the friend", "friend", "careful", can_manipulate=True),
]

CLUES = {
    "ticket stub": {"kind": "paper", "scent": "ink", "meaning": "someone had been near the front desk"},
    "bench note": {"kind": "paper", "scent": "pencil", "meaning": "someone left a short message and tried to hide it"},
    "coffee lid": {"kind": "cup", "scent": "coffee", "meaning": "someone had waited there long enough to drink quietly"},
    "door chain": {"kind": "metal", "scent": "dust", "meaning": "someone had checked the door and wanted it secure"},
    "mail slot": {"kind": "paper", "scent": "rain", "meaning": "someone slid a note in without being seen"},
    "umbrella": {"kind": "cloth", "scent": "wet", "meaning": "someone had come in from the rain"},
    "receipt": {"kind": "paper", "scent": "sweet", "meaning": "someone bought something small and secret"},
    "sugar packet": {"kind": "paper", "scent": "vanilla", "meaning": "someone stayed long enough for tea"},
    "tray cloth": {"kind": "cloth", "scent": "bread", "meaning": "someone moved trays and tried to clean the scene"},
    "clipboard": {"kind": "board", "scent": "soap", "meaning": "someone had checked names and times carefully"},
    "tea cup": {"kind": "cup", "scent": "mint", "meaning": "someone was waiting while trying to stay calm"},
    "window seat": {"kind": "wood", "scent": "sunlight", "meaning": "someone sat and watched the hallway for a while"},
}

KNOWLEDGE = {
    "manipulate": [
        (
            "What does it mean to manipulate something?",
            "To manipulate something means to handle it carefully or change it by using your hands, words, or plans."
        )
    ],
    "pregnancy": [
        (
            "What is pregnancy?",
            "Pregnancy is when a baby grows inside a person's body before the baby is born."
        )
    ],
    "suspense": [
        (
            "What is suspense in a story?",
            "Suspense is the feeling of waiting to find out what will happen next."
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues, asks questions, and tries to solve a mystery."
        )
    ],
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for clue in setting.clues:
            for suspect in SUSPECTS:
                combos.append((place, clue, suspect.id))
    return combos


def explain_invalid(place: str, clue: str, suspect: str) -> str:
    return (
        f"(No story: the clue '{clue}' does not fit a reasonable detective trail "
        f"with {suspect} at {place}.)"
    )


def reasonableness_gate(place: str, clue: str, suspect: str) -> bool:
    if place not in SETTINGS:
        return False
    if clue not in CLUES:
        return False
    if suspect not in {s.id for s in SUSPECTS}:
        return False
    return clue in _safe_lookup(SETTINGS, place).clues


def detect_manipulation(world: World, detective: Entity, suspect: Entity, clue: Entity) -> None:
    detective.memes["suspense"] += 1
    clue.meters["moved"] = clue.meters.get("moved", 0.0) + 1
    world.say(
        f"{detective.id} noticed that someone had manipulated the {clue.label}."
    )
    world.say(
        f"It was a small change, but in a mystery even small changes can matter."
    )


def infer_truth(world: World, detective: Entity, suspect: Entity, clue: Entity, pregnant: Entity) -> None:
    detective.memes["suspense"] += 1
    detective.memes["certainty"] = detective.memes.get("certainty", 0.0) + 1
    world.say(
        f"At last, {detective.id} understood the trail: the clue was not a warning of danger, "
        f"but a careful cover for a pregnancy secret."
    )
    world.say(
        f"{suspect.id} had been trying to protect {pregnant.pronoun('object')} by manipulating the clues "
        f"so the surprise would stay hidden."
    )


def resolve(world: World, detective: Entity, suspect: Entity, pregnant: Entity, clue: Entity) -> None:
    detective.memes["relief"] = detective.memes.get("relief", 0.0) + 1
    world.say(
        f"{detective.id} gave a small nod and closed the case."
    )
    world.say(
        f"The air in {world.setting.place} felt lighter now, and the hidden pregnancy was no longer a mystery."
    )
    world.say(
        f"By the end, the clue was put back in place, the secret was safe, and everyone could breathe again."
    )


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)

    detective_name, detective_type = next(
        (name, gender) for name, gender in DETECTIVES if name == params.detective
    )
    suspect_cfg = next(s for s in SUSPECTS if s.id == params.suspect)
    clue_info = _safe_lookup(CLUES, params.clue)

    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_type,
        role="detective",
    ))
    suspect = world.add(Entity(
        id=suspect_cfg.id,
        kind="character",
        type="person",
        label=suspect_cfg.label,
        role=suspect_cfg.role,
    ))
    pregnant = world.add(Entity(
        id="pregnant_person",
        kind="character",
        type="woman",
        label="the expectant mother",
        role="pregnant",
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type=clue_info["kind"],
        label=params.clue,
        role="clue",
    ))

    world.facts.update(
        detective=detective,
        suspect=suspect,
        pregnant=pregnant,
        clue=clue,
        place=params.place,
        pregnancy_secret=params.pregnancy_secret,
        clue_info=clue_info,
        suspect_cfg=suspect_cfg,
    )

    world.say(
        f"{detective.id} arrived at {world.setting.place} on a quiet morning, when the air felt "
        f"full of {world.setting.mood} suspense."
    )
    world.say(
        f"A small case had begun: someone had tried to manipulate the {clue.label}."
    )
    world.say(
        f"{suspect.label} looked worried, and the expectant mother kept one hand on her belly, "
        f"guarding a pregnancy secret."
    )

    world.para()
    world.say(
        f"{detective.id} looked at the {clue.label}, the smell of {clue_info['scent']}, and the place where it had been moved."
    )
    world.say(
        f"The clue's little shift made the whole room feel stranger, because in a detective story a changed clue can mean a hidden truth."
    )

    world.para()
    detect_manipulation(world, detective, suspect, clue)
    world.say(
        f"The trail led from the {clue.label} to {suspect.label}, and then to the expectant mother."
    )
    infer_truth(world, detective, suspect, clue, pregnant)
    resolve(world, detective, suspect, pregnant, clue)

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = _safe_fact(world, f, "detective")
    suspect = _safe_fact(world, f, "suspect_cfg").label
    clue = _safe_fact(world, f, "clue").label
    place = _safe_fact(world, f, "place")
    return [
        f"Write a short detective story with suspense set at {_safe_lookup(SETTINGS, place).place} where {detective.id} follows the clue '{clue}'.",
        f"Tell a mystery about someone who tried to manipulate a clue, and the answer leads to a pregnancy secret.",
        f"Write a child-friendly detective story with a careful reveal, a hidden pregnancy, and a calm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = _safe_fact(world, f, "detective")
    suspect = _safe_fact(world, f, "suspect_cfg")
    clue = _safe_fact(world, f, "clue")
    pregnant = _safe_fact(world, f, "pregnant")
    place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Who solved the mystery at {_safe_lookup(SETTINGS, place).place}?",
            answer=f"{detective.id}, the detective, solved the mystery by following the clue and asking careful questions."
        ),
        QAItem(
            question=f"What clue was manipulated in the story?",
            answer=f"The {clue.label} was manipulated, which made the case feel suspicious at first."
        ),
        QAItem(
            question=f"Why did {suspect.label} act so nervous?",
            answer=f"{suspect.label} was nervous because {suspect.label} had been trying to protect the pregnancy secret."
        ),
        QAItem(
            question="What did the detective learn at the end?",
            answer="The detective learned that the clue had been changed to keep a pregnancy secret safe, not to hurt anyone."
        ),
        QAItem(
            question=f"How did the story end at {_safe_lookup(SETTINGS, place).place}?",
            answer=f"It ended calmly, with the clue put back, the secret protected, and everyone feeling relief."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["detective"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["manipulate"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["pregnancy"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["suspense"])
    return out


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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:16} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
clue_changed(C) :- clue(C), moved(C).
mystery(C) :- clue_changed(C), pregnancy_secret(S).
resolved :- mystery(C), detective(D), suspect(X).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for clue in setting.clues:
            lines.append(asp.fact("clue_at", sid, clue))
    for clue in CLUES:
        lines.append(asp.fact("clue", clue))
    for s in SUSPECTS:
        lines.append(asp.fact("suspect", s.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show clue_at/2."))
    return sorted(set(asp.atoms(model, "clue_at")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective suspense story world with a pregnancy secret.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--detective", choices=[n for n, _ in DETECTIVES])
    ap.add_argument("--suspect", choices=[s.id for s in SUSPECTS])
    ap.add_argument("--clue", choices=list(CLUES))
    ap.add_argument("--pregnancy-secret", default="the baby was coming soon")
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
    if getattr(args, "place", None) and getattr(args, "clue", None) and not reasonableness_gate(getattr(args, "place", None), getattr(args, "clue", None), getattr(args, "suspect", None) or _safe_lookup(SUSPECTS, 0).id):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "clue", None) is None or c[1] == getattr(args, "clue", None))
              and (getattr(args, "suspect", None) is None or c[2] == getattr(args, "suspect", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, clue, suspect = rng.choice(list(combos))
    detective = getattr(args, "detective", None) or rng.choice([n for n, _ in DETECTIVES])
    return StoryParams(
        place=place,
        detective=detective,
        suspect=suspect,
        clue=clue,
        pregnancy_secret=getattr(args, "pregnancy_secret", None),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show clue_at/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show clue_at/2."))
        print(f"{len(asp.atoms(model, 'clue_at'))} compatible setting/clue pairs:")
        for place, clue in sorted(set(asp.atoms(model, "clue_at"))):
            print(f"  {place:10} {clue}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams("station", "Iris", "neighbor", "ticket stub", "the baby was coming soon"),
            StoryParams("apartment", "Nina", "brother", "door chain", "the baby was coming soon"),
            StoryParams("bakery", "Mara", "friend", "receipt", "the baby was coming soon"),
            StoryParams("clinic", "Eli", "clerk", "clipboard", "the baby was coming soon"),
        ]
        samples = [generate(p) for p in curated]
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
            header = f"### {p.detective} at {p.place} with {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
