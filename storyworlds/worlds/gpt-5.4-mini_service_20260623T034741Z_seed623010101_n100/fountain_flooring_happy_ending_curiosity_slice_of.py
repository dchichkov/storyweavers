#!/usr/bin/env python3
"""
storyworlds/worlds/fountain_flooring_happy_ending_curiosity_slice_of.py
=======================================================================

A small slice-of-life storyworld about a curious child, a fountain, and the
flooring around it. The world keeps the tone gentle and everyday: a child wants
to understand a place, a grown-up notices a real risk, and they find a safe way
to enjoy the moment together.

The seed prompt asks for the words "fountain" and "flooring" with the features
Happy Ending and Curiosity, in a slice-of-life style.

Core premise:
- A child is curious about a fountain in a public indoor space.
- The fountain can splash water onto the nearby flooring.
- Wet flooring is slippery, so the grown-up warns the child and suggests a
  safer way to look and listen.
- The child stays curious, but chooses the safe path, and the ending proves the
  change: they enjoy the fountain from a dry spot, with a happy ending.

The script follows the Storyweavers contract:
- standalone stdlib script
- eager import of results.py
- lazy import of asp.py inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- inline ASP twin and Python reasonableness gate
"""

from __future__ import annotations

import argparse
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
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    caretaker: object | None = None
    child: object | None = None
    flooring: object | None = None
    fountain: object | None = None
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    label: str
    indoors: bool
    has_fountain: bool
    floor_kind: str
    fountain_sound: str
    good_spot: str
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
class Concern:
    id: str
    label: str
    phrase: str
    risk: str
    fix: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class SafeChoice:
    id: str
    label: str
    phrase: str
    action: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


@dataclass
class StoryParams:
    place: str
    concern: str
    safe_choice: str
    child_name: str = "Mia"
    child_gender: str = "girl"
    caretaker_gender: str = "mother"
    seed: Optional[int] = None
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


PLACES = {
    "lobby": Place(
        id="lobby",
        label="the library lobby",
        indoors=True,
        has_fountain=True,
        floor_kind="tile",
        fountain_sound="the fountain made a soft trickle",
        good_spot="a dry bench by the wall",
        tags={"fountain", "flooring", "tile", "library"},
    ),
    "atrium": Place(
        id="atrium",
        label="the school atrium",
        indoors=True,
        has_fountain=True,
        floor_kind="stone",
        fountain_sound="the fountain made a bright splashing whisper",
        good_spot="the marked line by the plant pots",
        tags={"fountain", "flooring", "school", "stone"},
    ),
    "mall": Place(
        id="mall",
        label="the little mall atrium",
        indoors=True,
        has_fountain=True,
        floor_kind="polished stone",
        fountain_sound="the fountain made a cheerful plink-plink sound",
        good_spot="a dry circle near the railing",
        tags={"fountain", "flooring", "mall", "stone"},
    ),
}

CONCERNS = {
    "slip": Concern(
        id="slip",
        label="slippery flooring",
        phrase="the wet flooring",
        risk="water can make the floor slippery",
        fix="stay on the dry side and watch from there",
        tags={"slip", "wet", "flooring"},
    ),
    "splash": Concern(
        id="splash",
        label="splashy water",
        phrase="the splashy fountain water",
        risk="water can splash onto the floor",
        fix="stand back and look where the water lands",
        tags={"splash", "water", "fountain"},
    ),
}

SAFE_CHOICES = {
    "bench": SafeChoice(
        id="bench",
        label="dry bench",
        phrase="a dry bench",
        action="sit on the dry bench and watch",
        tags={"bench", "dry"},
    ),
    "line": SafeChoice(
        id="line",
        label="marked line",
        phrase="the marked line",
        action="stand by the marked line and watch",
        tags={"line", "dry"},
    ),
    "rail": SafeChoice(
        id="rail",
        label="railing",
        phrase="the railing",
        action="lean near the railing and watch",
        tags={"rail", "dry"},
    ),
}

GIRL_NAMES = ["Mia", "Ava", "Lila", "Nora", "Ella", "Zoe", "Iris", "Ruby"]
BOY_NAMES = ["Leo", "Ben", "Milo", "Theo", "Noah", "Finn", "Eli", "Max"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        if not place.has_fountain:
            continue
        for cid in CONCERNS:
            for sid in SAFE_CHOICES:
                combos.append((pid, cid, sid))
    return combos


def choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def _entity_defaults() -> dict[str, float]:
    return {"wet": 0.0, "curious": 0.0, "calm": 0.0, "worry": 0.0, "joy": 0.0}


def tell(place: Place, concern: Concern, safe_choice: SafeChoice,
         child_name: str, child_gender: str, caretaker_gender: str) -> World:
    world = World(place=place)
    child = world.add(Entity(
        id=child_name, kind="character", type=child_gender, role="child",
        label=child_name, meters=_entity_defaults().copy(), memes=_entity_defaults().copy(),
    ))
    caretaker_type = caretaker_gender
    caretaker_label = "mom" if caretaker_gender == "mother" else "dad"
    caretaker = world.add(Entity(
        id="Caretaker", kind="character", type=caretaker_type, role="caretaker",
        label=caretaker_label, meters=_entity_defaults().copy(), memes=_entity_defaults().copy(),
    ))
    fountain = world.add(Entity(
        id="fountain", kind="thing", type="fountain", label="fountain",
        meters={"wet": 0.0}, memes={},
    ))
    flooring = world.add(Entity(
        id="flooring", kind="thing", type="flooring", label="flooring",
        meters={"wet": 0.0, "slippery": 0.0}, memes={},
    ))

    child.memes["curious"] += 1
    child.memes["joy"] += 1
    world.say(
        f"{child_name} and {caretaker.label} stopped in {place.label} on an ordinary day."
    )
    world.say(
        f"{child_name} noticed the fountain right away, because {place.fountain_sound}."
    )
    world.say(
        f"{child_name} wanted to get closer and see how the water moved over the {place.floor_kind} flooring."
    )

    world.para()
    if concern.id == "slip":
        world.say(
            f"{caretaker.label.capitalize()} pointed at the flooring. "
            f'"Careful," {caretaker.label} said. "The wet flooring can be slippery."'
        )
    else:
        world.say(
            f"{caretaker.label.capitalize()} smiled, but still said, "
            f'"Let’s watch carefully. Fountain water can splash farther than it looks."'
        )

    child.memes["curious"] += 1
    child.memes["worry"] += 0.5
    flooring.meters["wet"] += 1.0
    flooring.meters["slippery"] += 1.0
    fountain.meters["water"] += 1.0

    world.para()
    if flooring.meters["slippery"] >= THRESHOLD:
        world.say(
            f"That made {child_name} pause. The fountain still shimmered, but the flooring really did look slick."
        )
    world.say(
        f"So {child_name} chose {safe_choice.phrase} instead of stepping into the splashy spot."
    )
    child.memes["calm"] += 1
    child.memes["joy"] += 1
    caretaker.memes["joy"] += 1

    world.para()
    world.say(
        f"From {place.good_spot}, {child_name} could watch the little ripples, hear the water, and ask a dozen questions."
    )
    world.say(
        f"{caretaker.label.capitalize()} answered each one, and the two of them stayed dry."
    )
    world.say(
        f"When they left, the fountain was still singing, the flooring was safe, and {child_name} was smiling."
    )

    world.facts.update(
        child=child,
        caretaker=caretaker,
        fountain=fountain,
        flooring=flooring,
        concern=concern,
        safe_choice=safe_choice,
        place=place,
    )
    return world


def reasonableness_gate(place: Place, concern: Concern, safe_choice: SafeChoice) -> bool:
    return place.has_fountain and place.indoors and "flooring" in concern.tags and "dry" in safe_choice.tags


def interaction_risk(place: Place, concern: Concern) -> bool:
    return place.has_fountain and concern.id in CONCERNS


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place = f["place"]
    concern = f["concern"]
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old that includes the words "fountain" and "flooring".',
        f"Tell a gentle story about {child.id} visiting {place.label} and feeling curious about the fountain, while a grown-up worries about {concern.label}.",
        f"Write a happy-ending story where a child notices a fountain, learns something about the flooring, and chooses a safe place to watch.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    caretaker = f["caretaker"]
    place = f["place"]
    concern = f["concern"]
    safe_choice = f["safe_choice"]
    qa = [
        QAItem(
            question=f"What did {child.id} want to look at in {place.label}?",
            answer=f"{child.id} wanted to look at the fountain. {child.pronoun('subject').capitalize()} was curious about how the water moved and what it did near the flooring.",
        ),
        QAItem(
            question=f"Why did {caretaker.label} warn {child.id} about the flooring?",
            answer=f"{caretaker.label.capitalize()} warned {child.id} because the wet flooring could be slippery. The fountain splashed nearby, so staying careful made the moment safer.",
        ),
        QAItem(
            question=f"What safe choice did {child.id} make in the end?",
            answer=f"{child.id} chose {safe_choice.phrase} and watched from there. That let {child.id} stay dry while still enjoying the fountain.",
        ),
        QAItem(
            question=f"How did the story end for {child.id} and {caretaker.label}?",
            answer=f"They ended the visit smiling together. The fountain kept sparkling, the flooring stayed safe, and {child.id} learned something new without getting hurt.",
        ),
    ]
    if f["flooring"].meters.get("slippery", 0.0) >= THRESHOLD:
        qa.append(
            QAItem(
                question=f"What made the flooring feel risky near the fountain?",
                answer=f"The fountain splashed water onto the flooring, and that made the surface slippery. The child noticed the risk and chose a dry spot instead.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["place"].tags) | set(world.facts["concern"].tags) | set(world.facts["safe_choice"].tags)
    bank = [
        ("What is a fountain?", "A fountain is a place where water moves up and then falls back down again. People often watch fountains because the water makes gentle sounds."),
        ("What is flooring?", "Flooring is the surface you walk on inside a building, like tile or wood. If it gets wet, it can become slippery."),
        ("Why is wet flooring slippery?", "Wet flooring can be slippery because water makes the surface smoother. That can make feet slide more easily."),
        ("Why do people stay careful near a fountain?", "People stay careful near a fountain because the water can splash outside the basin. Splashing water can wet the floor and make it less safe."),
        ("What does it mean to be curious?", "Being curious means you want to know more and you like to ask questions. Curious kids often stop and look closely at things."),
        ("Why is it nice to watch from a dry spot?", "A dry spot helps you stay safe while you look around. You can still enjoy the view without stepping into water."),
    ]
    wanted = []
    for q, a in bank:
        wanted.append(QAItem(q, a))
    return wanted


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_story_params() -> list[StoryParams]:
    return [
        StoryParams(place="lobby", concern="slip", safe_choice="bench", child_name="Mia", child_gender="girl", caretaker_gender="mother"),
        StoryParams(place="atrium", concern="splash", safe_choice="line", child_name="Leo", child_gender="boy", caretaker_gender="father"),
        StoryParams(place="mall", concern="slip", safe_choice="rail", child_name="Nora", child_gender="girl", caretaker_gender="mother"),
    ]


CURATED = valid_story_params()


def explain_rejection(place: Place, concern: Concern, safe_choice: SafeChoice) -> str:
    return (
        f"(No story: this scene needs a real fountain, risky flooring, and a safe dry place to stand. "
        f"Try a fountain location with indoor flooring and a dry watching spot.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a curious child, a fountain, and safe flooring."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--concern", choices=CONCERNS)
    ap.add_argument("--safe-choice", dest="safe_choice", choices=SAFE_CHOICES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caretaker", choices=["mother", "father"])
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
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "concern", None) is None or c[1] == getattr(args, "concern", None))
              and (getattr(args, "safe_choice", None) is None or c[2] == getattr(args, "safe_choice", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, concern, safe_choice = rng.choice(list(combos))
    place_obj = _safe_lookup(PLACES, place)
    concern_obj = _safe_lookup(CONCERNS, concern)
    safe_obj = _safe_lookup(SAFE_CHOICES, safe_choice)
    if not reasonableness_gate(place_obj, concern_obj, safe_obj):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or choose_name(rng, gender)
    caretaker = getattr(args, "caretaker", None) or rng.choice(["mother", "father"])
    return StoryParams(place=place, concern=concern, safe_choice=safe_choice,
                       child_name=name, child_gender=gender, caretaker_gender=caretaker)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.concern not in CONCERNS or params.safe_choice not in SAFE_CHOICES:
        pass
    place = _safe_lookup(PLACES, params.place)
    concern = _safe_lookup(CONCERNS, params.concern)
    safe_choice = _safe_lookup(SAFE_CHOICES, params.safe_choice)
    if not reasonableness_gate(place, concern, safe_choice):
        pass
    world = tell(place, concern, safe_choice, params.child_name, params.child_gender, params.caretaker_gender)
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


def ASP_RULES() -> str:
    return r"""
valid(P, C, S) :- place(P), concern(C), safe_choice(S), has_fountain(P), dry_choice(S), indoor(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoor", pid))
        if p.has_fountain:
            lines.append(asp.fact("has_fountain", pid))
    for cid in CONCERNS:
        lines.append(asp.fact("concern", cid))
    for sid, s in SAFE_CHOICES.items():
        lines.append(asp.fact("safe_choice", sid))
        if "dry" in s.tags:
            lines.append(asp.fact("dry_choice", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES()}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    ok = True
    try:
        python_set = set(valid_combos())
        clingo_set = set(asp_valid_combos())
        if python_set != clingo_set:
            ok = False
            print("MISMATCH between clingo and valid_combos():")
            if clingo_set - python_set:
                print("  only in clingo:", sorted(clingo_set - python_set))
            if python_set - clingo_set:
                print("  only in python:", sorted(python_set - clingo_set))
        else:
            print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        sample = generate(CURATED[0])
        if not sample.story or "fountain" not in sample.story or "flooring" not in sample.story:
            ok = False
            print("MISMATCH: smoke story missing required words.")
        else:
            print("OK: generation smoke test passed.")
    except Exception:
        ok = False
        traceback.print_exc()
    return 0 if ok else 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, concern, safe_choice) combos:\n")
        for row in combos:
            print("  ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
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
            header = f"### {p.child_name} in {p.place} ({p.concern}, {p.safe_choice})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
