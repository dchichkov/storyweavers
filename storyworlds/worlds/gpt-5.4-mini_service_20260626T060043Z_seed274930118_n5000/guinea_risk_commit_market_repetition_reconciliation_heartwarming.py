#!/usr/bin/env python3
"""
A heartwarming market storyworld about a guinea pig, a small risk, a firm
commitment, repetition, and reconciliation.

Premise:
- A little guinea pig loves helping at the market.
- The market is busy, and one repeated risk is that a small helper can get
  jostled, lose track of the basket, or make a stall owner worry.
- The child/animal commits to a careful task and repeats it well.
- A misunderstanding creates a small hurt, then a warm reconciliation closes
  the story.

The world model tracks meters and memes:
- meters: basket, crowd, carried, spilled, distance
- memes: worry, trust, stubbornness, relief, gratitude, bond
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
# Domain model
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    adult: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class Place:
    name: str = "the market"
    crowd_level: int = 2
    world: object | None = None
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


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    object_label: str
    object_phrase: str
    risk: str
    repeat_line: str
    repair: str
    keyword: str = ""
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
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace_notes: list[str] = field(default_factory=list)

    clone: object | None = None
    world: object | None = None
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
        import copy

        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone
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


THRESHOLD = 1.0
TOKENS = {"guinea", "risk", "commit", "repetition", "reconciliation", "heartwarming"}


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
NAMES = ["Pip", "Milo", "Nia", "Luna", "Ollie", "Tessa", "Poppy", "Junie"]
ADULTS = ["Aunt May", "Mr. Reed", "Mrs. Lark", "Uncle Ben"]
TRAITS = ["gentle", "curious", "brave", "patient", "cheerful"]

TASKS = {
    "berries": Task(
        id="berries",
        verb="carry berries to the fruit stall",
        gerund="carrying berries",
        object_label="basket",
        object_phrase="a small basket of berries",
        risk="the berries might spill if the crowd bumped into the basket",
        repeat_line="Again and again, the careful little paws kept the basket steady.",
        repair="gather the berries back into the basket and apologize",
        keyword="berries",
        tags={"market", "guinea", "risk", "repetition"},
    ),
    "bread": Task(
        id="bread",
        verb="bring warm bread to the baker's table",
        gerund="bringing bread",
        object_label="tray",
        object_phrase="a tray of warm bread rolls",
        risk="the soft rolls could slide if the tray tilted",
        repeat_line="Each time the path wiggled, the tray stayed flat and safe.",
        repair="set the bread right and smile kindly",
        keyword="bread",
        tags={"market", "risk", "commit", "repetition"},
    ),
    "flowers": Task(
        id="flowers",
        verb="deliver flowers to the corner stall",
        gerund="delivering flowers",
        object_label="bundle",
        object_phrase="a bundle of bright flowers",
        risk="the stems might bend if the bundle got squeezed",
        repeat_line="Step by step, the little helper repeated the same careful walk.",
        repair="straighten the flowers and speak softly",
        keyword="flowers",
        tags={"market", "repetition", "reconciliation"},
    ),
}

OUTCOMES = {
    "misunderstanding": "thought the helper had been careless",
    "apology": "said sorry with a soft voice",
    "reconcile": "smiled and forgave the mistake",
}


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def _narrate_setup(world: World, hero: Entity, adult: Entity, task: Task, item: Entity) -> None:
    world.say(
        f"{hero.id} was a small guinea pig with a big heart, and {hero.pronoun('possessive')} "
        f"{adult.label} trusted {hero.pronoun('object')} at the market."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved {task.gerund}, because helping made the busy stalls feel friendly."
    )
    world.say(
        f"One morning, {adult.label} gave {hero.pronoun('object')} {task.object_phrase}, and {hero.id} promised to be careful."
    )
    item.carried_by = hero.id
    hero.memes["trust"] += 1
    hero.memes["commitment"] += 1


def _risk_step(world: World, hero: Entity, task: Task, item: Entity) -> bool:
    # The market crowd creates repeated bumps; the risk is whether the item gets unstable.
    hero.meters["crowd"] = world.place.crowd_level
    if hero.memes.get("commitment", 0) < THRESHOLD:
        return False
    hero.memes["worry"] += 0.5
    item.meters["unstable"] = item.meters.get("unstable", 0.0) + 1.0
    world.say(
        f"The market was busy, and {task.risk}."
    )
    world.say(
        f"But {hero.id} kept going anyway, because {hero.pronoun('subject')} had made a promise."
    )
    return True


def _repetition(world: World, hero: Entity, task: Task, item: Entity) -> None:
    # Repetition makes the careful behavior visible and causal.
    for _ in range(2):
        hero.meters["steps"] = hero.meters.get("steps", 0.0) + 1.0
        hero.memes["stubbornness"] = hero.memes.get("stubbornness", 0.0) + 0.2
        world.say(task.repeat_line)
    item.meters["safe"] = item.meters.get("safe", 0.0) + 1.0
    hero.memes["trust"] += 0.5


def _misunderstanding(world: World, hero: Entity, adult: Entity, task: Task, item: Entity) -> None:
    adult.memes["worry"] = adult.memes.get("worry", 0.0) + 1.0
    hero.memes["hurt"] = hero.memes.get("hurt", 0.0) + 1.0
    world.say(
        f"Then a shopper brushed past, and {item.label} tipped a little."
    )
    world.say(
        f"{adult.label} {OUTCOMES['misunderstanding']}."
    )
    world.say(
        f"{hero.id} felt tiny and sad, because {hero.pronoun('subject')} had been trying so hard."
    )


def _reconcile(world: World, hero: Entity, adult: Entity, task: Task, item: Entity) -> None:
    if hero.memes.get("hurt", 0.0) < THRESHOLD:
        return
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1.0
    adult.memes["gratitude"] = adult.memes.get("gratitude", 0.0) + 1.0
    adult.memes["worry"] = 0.0
    hero.memes["hurt"] = 0.0
    hero.memes["bond"] = hero.memes.get("bond", 0.0) + 1.0
    world.say(
        f"{hero.id} took a breath, explained the promise, and {OUTCOMES['apology']}."
    )
    world.say(
        f"{adult.label} listened, saw the steady paws and the safe basket, and {OUTCOMES['reconcile']}."
    )
    world.say(
        f"At the end, {hero.id} and {adult.label} stood together in the market, with {item.label} neat and full again."
    )


def tell(place: Place, task: Task, hero_name: str, adult_name: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type="guinea pig", label="little guinea pig"))
    adult = world.add(Entity(id="Adult", kind="character", type="adult", label=adult_name))
    item = world.add(
        Entity(
            id="Item",
            kind="thing",
            type=task.object_label,
            label=task.object_label,
            phrase=task.object_phrase,
            owner=hero.id,
            caretaker=adult.id,
            carried_by=hero.id,
        )
    )

    _narrate_setup(world, hero, adult, task, item)
    world.para()
    if _risk_step(world, hero, task, item):
        _repetition(world, hero, task, item)
        _misunderstanding(world, hero, adult, task, item)
        world.para()
        _reconcile(world, hero, adult, task, item)

    world.facts.update(hero=hero, adult=adult, item=item, task=task, place=place)
    return world


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    task: str
    name: str
    adult: str
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


CURATED = [
    StoryParams(task="berries", name="Pip", adult="Aunt May"),
    StoryParams(task="bread", name="Milo", adult="Mrs. Lark"),
    StoryParams(task="flowers", name="Nia", adult="Mr. Reed"),
]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    task = _safe_fact(world, f, "task")
    adult = _safe_fact(world, f, "adult")
    return [
        f'Write a heartwarming story about a guinea pig named {hero.id} at the market, '
        f"where {hero.id} makes a promise, repeats a careful action, and then reconciles "
        f"with {adult.label}. Include the word '{task.keyword}'.",
        f"Tell a small story set in the market about {hero.id} and a risk that gets resolved by commitment and kindness.",
        f"Write a gentle story with repetition and reconciliation in which {hero.id} helps carry {task.object_phrase}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, adult, task, item, place = f["hero"], f["adult"], f["task"], f["item"], f["place"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a small guinea pig with a big heart, and {adult.label} at the market.",
        ),
        QAItem(
            question=f"What did {hero.id} promise to do?",
            answer=f"{hero.id} promised to be careful while {task.verb}, and {hero.pronoun('subject')} kept that promise.",
        ),
        QAItem(
            question=f"Why was there a risk during the trip through {place.name}?",
            answer=f"There was a risk because the market was busy, and {task.risk}.",
        ),
        QAItem(
            question=f"What repeated action helped the story go well?",
            answer=f"{hero.id} repeated the same careful steps while {task.gerund}, and that steady repetition kept {item.label} safe.",
        ),
        QAItem(
            question=f"How did the misunderstanding end?",
            answer=f"{hero.id} explained what happened, {adult.label} listened, and they reconciled with warmth and kindness.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "guinea": (
        "What is a guinea pig?",
        "A guinea pig is a small furry animal that likes gentle hands, safe spaces, and tasty snacks.",
    ),
    "risk": (
        "What does risk mean?",
        "Risk means something could go wrong, so you take care to stay safe.",
    ),
    "commit": (
        "What does it mean to commit to something?",
        "To commit means to promise you will do it and keep trying even when it is a little hard.",
    ),
    "repetition": (
        "Why can repetition help?",
        "Repetition can help because doing the same careful thing again and again can make it easier and safer.",
    ),
    "reconciliation": (
        "What is reconciliation?",
        "Reconciliation is when people who had a problem make peace again and feel close once more.",
    ),
    "market": (
        "What is a market?",
        "A market is a place where people buy and sell food, flowers, and other useful things.",
    ),
    "heartwarming": (
        "What does heartwarming mean?",
        "Heartwarming means something makes people feel warm, happy, and kindly inside.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["task"].tags) | {"guinea", "risk", "commit", "repetition", "reconciliation", "heartwarming", "market"}
    out = []
    for key in ["guinea", "risk", "commit", "repetition", "reconciliation", "market", "heartwarming"]:
        if key in tags:
            q, a = WORLD_KNOWLEDGE[key]
            out.append(QAItem(question=q, answer=a))
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
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when the market setting, guinea-pig protagonist, and task all exist.
valid_story(T) :- task(T).

% The story must include the key instruments and theme words.
has_theme(T) :- task(T), keyword(T, guinea), keyword(T, risk), keyword(T, commit),
                keyword(T, repetition), keyword(T, reconciliation), keyword(T, heartwarming).

% A task is acceptable if it happens in the market.
market_story(T) :- task(T), place(T, market).

% Repetition and reconciliation are part of the intended arc.
arc_ok(T) :- task(T), repeats(T), reconciles(T), market_story(T).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = [asp.fact("place", "market")]
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("keyword", tid, "guinea"))
        lines.append(asp.fact("keyword", tid, "risk"))
        lines.append(asp.fact("keyword", tid, "commit"))
        lines.append(asp.fact("keyword", tid, "repetition"))
        lines.append(asp.fact("keyword", tid, "reconciliation"))
        lines.append(asp.fact("keyword", tid, "heartwarming"))
        lines.append(asp.fact("repeats", tid))
        lines.append(asp.fact("reconciles", tid))
        lines.append(asp.fact("place", tid, "market"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show market_story/1. #show arc_ok/1."))
    atoms = set((sym.name, tuple(a.name if a.type != a.type.Number and a.type != a.type.String else (a.number if a.type == a.type.Number else a.string) for a in sym.arguments)) for sym in model)
    expected = {("market_story", ("berries",)), ("market_story", ("bread",)), ("market_story", ("flowers",)),
                ("arc_ok", ("berries",)), ("arc_ok", ("bread",)), ("arc_ok", ("flowers",))}
    if atoms != expected:
        print("MISMATCH between ASP and Python story-registry expectations.")
        print("ASP:", sorted(atoms))
        print("PY :", sorted(expected))
        return 1
    print("OK: ASP and Python expectations agree.")
    return 0


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming market storyworld about a guinea pig, risk, commitment, repetition, and reconciliation.")
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--adult", choices=ADULTS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    task = getattr(args, "task", None) or rng.choice(list(TASKS))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    adult = getattr(args, "adult", None) or rng.choice(ADULTS)
    return StoryParams(task=task, name=name, adult=adult)


def generate(params: StoryParams) -> StorySample:
    world = tell(Place(), _safe_lookup(TASKS, params.task), params.name, params.adult)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show market_story/1. #show arc_ok/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_program("#show market_story/1. #show arc_ok/1."))
        print(sorted((sym.name, tuple(a.name if a.type != a.type.Number and a.type != a.type.String else (a.number if a.type == a.type.Number else a.string) for a in sym.arguments)) for sym in model))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
            header = f"### {p.name}: {p.task} at the market"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
