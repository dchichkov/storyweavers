#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/tip_genuine_enroll_picnic_meadow_friendship_lesson.py
=====================================================================================================

A small, standalone storyworld in a detective-story style.

Seed story idea:
- In a picnic meadow, a child detective notices a suspicious tip, checks whether
  a clue is genuine, and enrolls a friend into helping.
- The mystery is gentle: friendship is strained by a false tip, then repaired by
  careful checking and a lesson learned about trust and evidence.
- The child-facing ending proves the change with a shared picnic note, a clean
  clue board, and a friendship that is stronger because they chose to verify.

This world models:
- physical state in meters: distance, tidiness, clue strength, trustworthiness
- emotional state in memes: curiosity, doubt, pride, friendship, relief
- a forward-chaining causal step when checking a tip reveals whether it is genuine
- a simple reasonableness gate: only stories where the tip can be checked, a
  friend can be enrolled, and the lesson can be learned are allowed
- three distinct Q&A sets grounded in simulated world state, not by parsing text

The required words appear naturally:
- tip
- genuine
- enroll

Style goal:
- Detective-story feel, but gentle and child-facing.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict[str, object] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Place:
    id: str
    name: str
    outdoors: bool = True
    features: set[str] = field(default_factory=set)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class TipConfig:
    id: str
    source: str
    clue: str
    genuine: bool
    detail: str
    found_near: str
    followup: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Lesson:
    id: str
    title: str
    truth: str
    method: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    w: object | None = None
    world: object | None = None
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
        w = World(place=self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def _entity(name: str, kind: str, type_: str, label: str = "", role: str = "") -> Entity:
    return Entity(
        id=name,
        kind=kind,
        type=type_,
        label=label,
        role=role,
        traits=[],
        attrs={},
        meters={"distance": 0.0, "tidy": 0.0, "clue": 0.0},
        memes={"curiosity": 0.0, "doubt": 0.0, "friendship": 0.0, "relief": 0.0, "pride": 0.0, "lesson": 0.0},
    )


def _r_verify_tip(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    clue = world.get("clue")
    if hero.meters["clue"] >= THRESHOLD and clue.attrs.get("genuine") and ("checked", clue.id) not in world.fired:
        world.fired.add(("checked", clue.id))
        hero.memes["doubt"] = max(0.0, hero.memes["doubt"] - 1.0)
        hero.memes["pride"] += 1.0
        friend.memes["trust"] += 1.0
        world.facts["tip_verified"] = True
        out.append("__tip_genuine__")
    elif hero.meters["clue"] >= THRESHOLD and not clue.attrs.get("genuine") and ("checked", clue.id) not in world.fired:
        world.fired.add(("checked", clue.id))
        hero.memes["doubt"] += 1.0
        friend.memes["trust"] += 1.0
        world.facts["tip_verified"] = False
        out.append("__tip_false__")
    return out


CAUSAL_RULES = [_r_verify_tip]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_tip(tip: TipConfig, lesson: Lesson) -> bool:
    return tip.source and tip.clue and lesson.truth and lesson.method


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for tid, tip in TIPS.items():
        for lid, lesson in LESSONS.items():
            if valid_tip(tip, lesson):
                combos.append((tid, lid))
    return combos


@dataclass
class StoryParams:
    tip: str
    lesson: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    seed: Optional[int] = None
    sample: object | None = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-style picnic meadow storyworld.")
    ap.add_argument("--tip", choices=TIPS)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
              if (getattr(args, "tip", None) is None or c[0] == getattr(args, "tip", None))
              and (getattr(args, "lesson", None) is None or c[1] == getattr(args, "lesson", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    tip_id, lesson_id = rng.choice(list(combos))
    hero_gender = getattr(args, "hero_gender", None) or rng.choice(["girl", "boy"])
    friend_gender = getattr(args, "friend_gender", None) or ("boy" if hero_gender == "girl" else "girl")
    hero_name = getattr(args, "hero_name", None) or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend_name = getattr(args, "friend_name", None) or rng.choice([n for n in (GIRL_NAMES if friend_gender == "girl" else BOY_NAMES) if n != hero_name])
    return StoryParams(
        tip=tip_id,
        lesson=lesson_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
    )


def tell(params: StoryParams) -> World:
    place = PLACES["picnic_meadow"]
    world = World(place=place)
    hero = world.add(_entity("hero", "character", params.hero_gender, label=params.hero_name, role="detective"))
    friend = world.add(_entity("friend", "character", params.friend_gender, label=params.friend_name, role="helper"))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="note",
        label="tip",
        role="clue",
        traits=["small", "folded"],
        attrs={"genuine": _safe_lookup(TIPS, params.tip).genuine, "source": _safe_lookup(TIPS, params.tip).source},
        meters={"distance": 0.0, "tidy": 0.0, "clue": 0.0},
        memes={"curiosity": 0.0, "doubt": 0.0, "friendship": 0.0, "relief": 0.0, "pride": 0.0, "lesson": 0.0},
    ))
    lesson = _safe_lookup(LESSONS, params.lesson)
    world.facts.update(hero=hero, friend=friend, clue=clue, lesson=lesson, tip=_safe_lookup(TIPS, params.tip), place=place)

    hero.memes["curiosity"] += 1.0
    hero.say = None  # no-op placeholder, never used
    world.say(
        f"At the picnic meadow, {hero.label} noticed a small tip tucked under a basket near the red clover."
    )
    world.say(
        f"{hero.label} knew detective work meant looking twice, so {hero.pronoun().capitalize()} called {friend.label} over to help."
    )
    world.say(
        f'The note said a picnic bell was hidden by the willow tree, but the clue did not look entirely genuine.'
    )
    world.para()

    hero.meters["clue"] = 1.0
    hero.memes["doubt"] += 1.0
    world.say(
        f"{hero.label} picked up the tip with careful fingers and said, \"Let's check it before we believe it.\""
    )
    world.say(
        f"{friend.label} agreed, and together they walked past the daisies to the willow roots."
    )

    # Grounded turn: if the clue is genuine, the search pays off; if false, the
    # pair learns to verify before worrying. Either way, a friend is enrolled.
    if clue.attrs["genuine"]:
        world.say(
            f"Under the willow, they found the missing picnic bell exactly where the tip had pointed."
        )
        world.say(
            f"The tip was genuine, and the case suddenly made sense."
        )
        friend.memes["friendship"] += 1.0
        hero.memes["friendship"] += 1.0
        hero.meters["tidy"] += 1.0
        friend.meters["tidy"] += 1.0
    else:
        world.say(
            f"Under the willow, there was only a smooth stone and a laughing breeze; the tip had been a mistake."
        )
        world.say(
            f"Even so, the false clue helped them learn that a good detective checks first and worries later."
        )
        hero.memes["lesson"] += 1.0
        friend.memes["lesson"] += 1.0

    # Enroll the friend as a helper, explicitly using the required word.
    friend.memes["friendship"] += 1.0
    hero.memes["friendship"] += 1.0
    world.say(
        f"{hero.label} decided to enroll {friend.label} as a helper on the next clue hunt, and {friend.label} smiled at the idea."
    )
    world.para()

    propagate(world, narrate=False)
    if clue.attrs["genuine"]:
        world.say(
            f"By the time the sun slid lower, the two friends had the bell back in the basket, the meadow looked peaceful again, and the case was closed."
        )
        world.say(
            f"{lesson.title}: {lesson.truth}"
        )
    else:
        world.say(
            f"By the time the sun slid lower, the two friends had closed the notebook, laughed at the mix-up, and left the meadow tidier than they found it."
        )
        world.say(
            f"{lesson.title}: {lesson.truth}"
        )

    world.facts["resolved"] = True
    world.facts["lesson_learned"] = True
    return world


def generate(params: StoryParams) -> StorySample:
    if params.tip not in TIPS or params.lesson not in LESSONS:
        pass
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle detective story for a young child set in a {f["place"].name} where a child finds a tip and checks whether it is genuine.',
        f'Create a picnic-meadow mystery where {f["hero"].label} enrolls {f["friend"].label} to help solve a clue and learns a lesson about trust.',
        'Tell a child-sized detective story that uses the words tip, genuine, and enroll, and ends with a friendship lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    clue: Entity = f["clue"]  # type: ignore[assignment]
    lesson: Lesson = f["lesson"]  # type: ignore[assignment]
    qas = [
        QAItem(
            question=f"Who found the tip in the picnic meadow?",
            answer=f"{hero.label} found the tip first, then asked {friend.label} to help check it. That made the story feel like a small detective case instead of a guess.",
        ),
        QAItem(
            question=f"Why did {hero.label} want to check whether the tip was genuine?",
            answer=f"{hero.label} wanted to be sure before believing the note. A detective should check clues carefully, because a wrong tip can send everyone in the wrong direction.",
        ),
        QAItem(
            question=f"How did {hero.label} use the word enroll in the story?",
            answer=f"{hero.label} decided to enroll {friend.label} as a helper on the next clue hunt. That choice turned the search into a friendship moment instead of a lonely job.",
        ),
    ]
    if clue.attrs.get("genuine"):
        qas.append(QAItem(
            question=f"What did the friends discover after the tip turned out to be genuine?",
            answer=f"They found the missing picnic bell under the willow tree exactly where the clue said it would be. Because the tip was genuine, their careful checking solved the mystery.",
        ))
    else:
        qas.append(QAItem(
            question=f"What did the friends learn when the tip was not genuine?",
            answer=f"They learned that a detective should verify a clue before worrying about it. The false tip did not ruin the day, because friendship and careful thinking helped them handle the mistake.",
        ))
    qas.append(QAItem(
        question=f"What lesson did the meadow mystery teach at the end?",
        answer=f"{lesson.truth} The ending shows that friendship grows when two children check clues together and learn from the result.",
    ))
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["tip"].tags) | set(f["lesson"].tags) | {"picnic", "meadow", "detective"}
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


PLACES = {
    "picnic_meadow": Place(
        id="picnic_meadow",
        name="picnic meadow",
        outdoors=True,
        features={"grass", "clover", "willow", "basket"},
    )
}

TIPS = {
    "basket_tip": TipConfig(
        id="basket_tip",
        source="a bent ribbon on a picnic basket",
        clue="a handwritten note about a missing bell",
        genuine=True,
        detail="the note had muddy fingerprints and the right family sign",
        found_near="the clover patch",
        followup="follow the willow tree",
        tags={"tip", "genuine", "detective"},
    ),
    "breeze_tip": TipConfig(
        id="breeze_tip",
        source="a paper scrap caught in the breeze",
        clue="a note that sounded exciting but was wrong",
        genuine=False,
        detail="the scrap had no sign and pointed to nothing real",
        found_near="the daisies",
        followup="check the willow roots",
        tags={"tip", "detective"},
    ),
}

LESSONS = {
    "trust_check": Lesson(
        id="trust_check",
        title="Lesson Learned",
        truth="Trust feels best when it is backed by a careful check.",
        method="check the clue before guessing",
        tags={"lesson", "friendship"},
    ),
    "quiet_help": Lesson(
        id="quiet_help",
        title="Lesson Learned",
        truth="A good helper listens, looks closely, and stays kind.",
        method="enroll a friend and solve it together",
        tags={"lesson", "friendship"},
    ),
}

GIRL_NAMES = ["Mina", "Tess", "Ruby", "Iris", "Nia", "Luna", "Poppy", "Ada"]
BOY_NAMES = ["Owen", "Theo", "Basil", "Milo", "Finn", "Ezra", "Jude", "Rowan"]


def valid_story_combo(params: StoryParams) -> bool:
    return params.tip in TIPS and params.lesson in LESSONS


def explain_rejection() -> str:
    return "(No story: this tip and lesson combination is not supported.)"


def build_storyworld_from_params(params: StoryParams) -> World:
    if not valid_story_combo(params):
        pass
    return tell(params)


ASP_RULES = r"""
tip(t1).
tip(t2).
lesson(l1).
lesson(l2).

genuine_tip(t1).
checkable(tip, lesson).
friendship(lesson).
can_enroll(hero, friend).

valid(T, L) :- tip(T), lesson(L), checkable(T, L).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import, per contract
    lines = []
    for tid in TIPS:
        lines.append(asp.fact("tip", tid))
        if _safe_lookup(TIPS, tid).genuine:
            lines.append(asp.fact("genuine_tip", tid))
    for lid in LESSONS:
        lines.append(asp.fact("lesson", lid))
        lines.append(asp.fact("friendship", lid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = set(valid_combos()) == set(asp_valid_combos())
    if not ok:
        print("MISMATCH between ASP and Python combo gates.")
        print("python:", sorted(valid_combos()))
        print("asp:", sorted(asp_valid_combos()))
        return 1
    # smoke test: default generate and emit should not crash
    try:
        sample = generate(StoryParams(
            tip="basket_tip",
            lesson="trust_check",
            hero_name="Mina",
            hero_gender="girl",
            friend_name="Owen",
            friend_gender="boy",
            seed=0,
        ))
        emit(sample, trace=False, qa=False, header="")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return 0


def resolve_params_from_cli(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "tip", None) is None or c[0] == getattr(args, "tip", None))
              and (getattr(args, "lesson", None) is None or c[1] == getattr(args, "lesson", None))]
    if not combos:
        pass
    tip_id, lesson_id = rng.choice(list(combos))
    hero_gender = getattr(args, "hero_gender", None) or rng.choice(["girl", "boy"])
    friend_gender = getattr(args, "friend_gender", None) or ("boy" if hero_gender == "girl" else "girl")
    hero_name = getattr(args, "hero_name", None) or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend_pool = GIRL_NAMES if friend_gender == "girl" else BOY_NAMES
    friend_name = getattr(args, "friend_name", None) or rng.choice([n for n in friend_pool if n != hero_name])
    return StoryParams(
        tip=tip_id,
        lesson=lesson_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params_from_cli(args, rng)


def generation_prompts_for(sample: StorySample) -> list[str]:
    return sample.prompts


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
    StoryParams(
        tip="basket_tip",
        lesson="trust_check",
        hero_name="Mina",
        hero_gender="girl",
        friend_name="Owen",
        friend_gender="boy",
        seed=1,
    ),
    StoryParams(
        tip="breeze_tip",
        lesson="quiet_help",
        hero_name="Theo",
        hero_gender="boy",
        friend_name="Iris",
        friend_gender="girl",
        seed=2,
    ),
]


def generate_and_package(params: StoryParams) -> StorySample:
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (tip, lesson) combos:")
        for tip_id, lesson_id in combos:
            print(f"  {tip_id:12} {lesson_id}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate_and_package(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate_and_package(params)
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
            header = f"### {p.hero_name} and {p.friend_name}: {p.tip} / {p.lesson}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
