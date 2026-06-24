#!/usr/bin/env python3
"""
storyworlds/worlds/comic_love_gerund_misunderstanding_fable.py
==============================================================

A small fable-like story world about a comic book, a loving gerund, and a
misunderstanding that clears up with kindness.

Seed tale idea:
---
A little mouse loved reading comic books under the oak tree. One day, she laughed
at a comic strip where a bear slipped on a banana peel. A nearby owl thought she
was laughing at the bear itself and told the other animals that the mouse was
mean. The mouse explained the joke, the owl apologized, and the animals laughed
together at the comic instead of each other.

World model:
---
- Characters have physical meters and emotional memes.
- A comic book can be loved, read, dropped, misunderstood, and explained.
- A misunderstanding raises worry and hurt; an explanation lowers them and
  restores trust.
- The prose is narrated as a simple fable with an ending image and a moral.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- build_parser, resolve_params, generate, emit, main
- --verify, --asp, --show-asp, --json, --qa, --trace, --all, -n, --seed
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    comic: object | None = None
    hero: object | None = None
    observer: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"mouse", "girl", "mother", "woman", "does"}
        male = {"boy", "father", "man", "buck", "stag"}
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
class Setting:
    place: str = "the old oak tree"
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
class Comic:
    id: str
    title: str
    phrase: str
    pages: int
    joke: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class StoryParams:
    place: str
    comic: str
    name: str
    gender: str
    observer: str
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


@dataclass
class Rule:
    name: str
    apply: callable
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


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    mouse = world.get("hero")
    observer = world.get("observer")
    comic = world.get("comic")
    if mouse.memes.get("laugh", 0) >= THRESHOLD and not world.fired.__contains__(("misunderstanding",)):
        world.fired.add(("misunderstanding",))
        observer.memes["worry"] = observer.memes.get("worry", 0) + 1
        mouse.memes["hurt"] = mouse.memes.get("hurt", 0) + 1
        out.append(f"{observer.id} thought the laughter was unkind.")
    return out


def _r_explain(world: World) -> list[str]:
    out: list[str] = []
    mouse = world.get("hero")
    observer = world.get("observer")
    comic = world.get("comic")
    if mouse.memes.get("hurt", 0) >= THRESHOLD and observer.memes.get("worry", 0) >= THRESHOLD:
        sig = ("explain",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        observer.memes["worry"] = 0
        observer.memes["trust"] = observer.memes.get("trust", 0) + 1
        mouse.memes["hurt"] = 0
        mouse.memes["joy"] = mouse.memes.get("joy", 0) + 1
        out.append(f"The mouse explained the comic joke, and the worry melted away.")
    return out


def _r_shared_laughter(world: World) -> list[str]:
    out: list[str] = []
    mouse = world.get("hero")
    observer = world.get("observer")
    comic = world.get("comic")
    if observer.memes.get("trust", 0) >= THRESHOLD and not world.fired.__contains__(("shared_laughter",)):
        world.fired.add(("shared_laughter",))
        mouse.memes["joy"] = mouse.memes.get("joy", 0) + 1
        observer.memes["joy"] = observer.memes.get("joy", 0) + 1
        comic.meters["read"] = comic.meters.get("read", 0) + 1
        out.append(f"Then they laughed together at the comic instead of at one another.")
    return out


CAUSAL_RULES = [
    Rule("misunderstanding", _r_misunderstanding),
    Rule("explain", _r_explain),
    Rule("shared_laughter", _r_shared_laughter),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setup_world() -> dict[str, Setting]:
    return {
        "oak": Setting(place="the old oak tree", affords={"read"}),
        "meadow": Setting(place="the sunny meadow", affords={"read"}),
        "porch": Setting(place="the quiet porch", affords={"read"}),
    }


SETTINGS = setup_world()

COMICS = {
    "banana": Comic(
        id="banana",
        title="The Banana Peel Blunder",
        phrase="a small comic book with bright panels",
        pages=8,
        joke="a bear slipping on a banana peel",
        tags={"comic", "laugh"},
    ),
    "moon": Comic(
        id="moon",
        title="The Moon Hat Parade",
        phrase="a cheerful comic book with round moon pictures",
        pages=10,
        joke="a fox wearing a moon-shaped hat",
        tags={"comic", "kind"},
    ),
    "rain": Comic(
        id="rain",
        title="The Rainy Day Ribbon",
        phrase="a little comic book with blue raindrops",
        pages=6,
        joke="a duck dancing in puddles",
        tags={"comic", "gentle"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Tia", "Pia", "Ivy", "Rosa", "Maya"]
BOY_NAMES = ["Ben", "Toby", "Theo", "Niko", "Eli", "Sam", "Finn", "Leo"]
TRAITS = ["curious", "gentle", "cheerful", "thoughtful", "playful", "patient"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for comic_id in setting.affords and COMICS:
            combos.append((place, comic_id))
    return combos


def explain_rejection(place: str, comic_id: str) -> str:
    if place not in SETTINGS:
        return "(No story: the setting is not available.)"
    if comic_id not in COMICS:
        return "(No story: the comic is not available.)"
    return "(No story: this world only tells stories where a comic can be read in a quiet place.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    observer = _safe_fact(world, f, "observer")
    comic = _safe_fact(world, f, "comic")
    return [
        f'Write a short fable for a young child about a comic book and a misunderstanding.',
        f"Tell a gentle story where {hero.id} loves reading {comic.title} but {observer.id} thinks the laughter is unkind, then they clear up the misunderstanding.",
        f'Write a child-friendly fable that includes the word "comic" and ends with a kind lesson about listening before judging.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    observer = _safe_fact(world, f, "observer")
    comic = _safe_fact(world, f, "comic")
    setting = _safe_fact(world, f, "setting")
    qa = [
        QAItem(
            question=f"What did {hero.id} love to do at {setting.place}?",
            answer=f"{hero.id} loved reading {comic.title} under the trees, and the comic made {hero.pronoun('object')} smile.",
        ),
        QAItem(
            question=f"Why did {observer.id} get upset when {hero.id} laughed?",
            answer=f"{observer.id} thought {hero.id} was laughing at {comic.joke} in a mean way, so {observer.pronoun('subject')} worried at first.",
        ),
        QAItem(
            question=f"What fixed the misunderstanding in the story?",
            answer=f"{hero.id} explained the joke in the comic, and then {observer.id} understood that the laughter was kind and shared.",
        ),
        QAItem(
            question=f"Where did the story happen?",
            answer=f"It happened at {setting.place}, a calm place where the comic could be read peacefully.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did {hero.id} and {observer.id} feel at the end?",
                answer=f"They felt happy and friendly again, and they laughed together while the comic stayed open beside them.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    comic = _safe_fact(world, world.facts, "comic")
    return [
        QAItem(
            question="What is a comic book?",
            answer="A comic book tells a story with pictures and words together.",
        ),
        QAItem(
            question="Why should people ask before judging?",
            answer="People should ask first because a quick guess can be wrong, and asking helps prevent hurt feelings.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def tell(setting: Setting, comic_cfg: Comic, hero_name: str, hero_type: str, observer_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_type,
        label=hero_name,
        traits=["little", trait],
    ))
    observer = world.add(Entity(
        id="observer",
        kind="character",
        type=observer_type,
        label="the owl",
        traits=["careful", "watchful"],
    ))
    comic = world.add(Entity(
        id="comic",
        type="book",
        label="comic book",
        phrase=comic_cfg.phrase,
        meters={"read": 0.0},
    ))

    world.say(f"At {setting.place}, there lived a little {trait} {hero.type} named {hero_name}.")
    world.say(
        f"{hero_name} loved reading {comic_cfg.title}; the comic was {comic_cfg.phrase}, "
        f"and the little pages always made {hero.pronoun('object')} smile."
    )
    world.para()
    world.say(
        f"One day, {hero_name} sat with the comic and laughed at the picture of {comic_cfg.joke}."
    )
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.meters["read"] = hero.meters.get("read", 0) + 1
    observer.memes["worry"] = observer.memes.get("worry", 0) + 1
    world.say(
        f"Nearby, {observer.label} heard the laughter and thought it was aimed at someone else."
    )
    propagate(world, narrate=True)
    world.para()
    if observer.memes.get("worry", 0) >= THRESHOLD:
        world.say(
            f"{hero_name} looked up and said, "
            f'"I was laughing at the comic, not at any friend."'
        )
        propagate(world, narrate=True)
    world.para()
    world.say(
        f"In the end, {hero_name} and {observer.label} sat together under the branches, "
        f"sharing the comic and the warm afternoon."
    )
    world.say("A wise heart asks before it judges, and kindness turns confusion into friendship.")
    world.facts.update(
        hero=hero,
        observer=observer,
        comic=comic,
        setting=setting,
        resolved=observer.memes.get("trust", 0) >= THRESHOLD,
    )
    return world


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a comic, a loving gerund, and a misunderstanding in fable style."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--comic", choices=COMICS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--observer", choices=["owl", "crow", "fox"])
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    comic = getattr(args, "comic", None) or rng.choice(list(COMICS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    observer = getattr(args, "observer", None) or rng.choice(["owl", "crow", "fox"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    if place not in SETTINGS or comic not in COMICS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, comic=comic, name=name, gender=gender, observer=observer, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(COMICS, params.comic),
        params.name,
        "mouse" if params.gender == "girl" else "mouse",
        params.observer,
        params.trait,
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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid, comic in COMICS.items():
        lines.append(asp.fact("comic", cid))
        lines.append(asp.fact("comic_pages", cid, comic.pages))
        for tag in sorted(comic.tags):
            lines.append(asp.fact("tagged", cid, tag))
    return "\n".join(lines)


ASP_RULES = r"""
% A story is valid when a place affords reading and there is a comic there.
valid_story(P, C) :- affords(P, read), comic(C).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set((p, c) for p, c in valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(place="oak", comic="banana", name="Mina", gender="girl", observer="owl", trait="curious"),
    StoryParams(place="meadow", comic="moon", name="Leo", gender="boy", observer="crow", trait="gentle"),
    StoryParams(place="porch", comic="rain", name="Nora", gender="girl", observer="fox", trait="thoughtful"),
]


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str]]:
    return [(p, c) for p in SETTINGS for c in COMICS if _safe_lookup(SETTINGS, p).affords]


def build_story(params: StoryParams) -> StorySample:
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, comic) combos:\n")
        for place, comic in combos:
            print(f"  {place:8} {comic:8}")
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
            header = f"### {p.name}: {p.comic} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
