#!/usr/bin/env python3
"""
Fairy-tale storyworld: a small magical domain where a worried child learns that
gentle words and honest help can ease a hard day.

Seed tale inspiration:
---
A little girl named Ada lives beside a willow tree and a quiet brook. One day,
she finds a tiny spellbook with a silver ribbon and tries to use magic to fix
everything by herself. But the charm goes wrong, and the brook becomes tangled
with thorny reeds. Ada feels upset until a kind fairy tells her that some magic
works best with patience, sharing, and a little care. Ada listens, asks for
help, and learns the lesson. In the end, the brook sparkles again, and Ada goes
home smiling.

This world models:
- a fairy tale setting with a tiny problem,
- a magical tool that can make things easier,
- a lesson learned when the hero stops rushing,
- a happy ending image that proves the change.

The words "category" and "ease" are intentionally present because they are part
of the seed vocabulary for this generated world.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    magical: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    companion: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "fairy"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "wizard"}:
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
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)
    SETTING: object | None = None
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
class Goal:
    id: str
    want: str
    attempt: str
    lesson: str
    fix: str
    magic_word: str
    consequence: str
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
class Charm:
    id: str
    label: str
    phrase: str
    helps: set[str]
    eases: set[str]
    solution: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        return w


SETTING = Setting(
    place="the willow brook",
    detail="The willow branches brushed the water, and moonlight made the stones glow.",
    affords={"mend_brook", "find_blossoms", "sing_spell"},
)

GOALS = {
    "brook": Goal(
        id="brook",
        want="make the brook clear and bright",
        attempt="fix the brook alone",
        lesson="some problems become easier when you ask for help",
        fix="listen to the fairy and work together",
        magic_word="sparkle",
        consequence="the tangled reeds loosened and the water shone again",
        tags={"brook", "water", "lesson", "category", "ease", "magic"},
    ),
    "rose": Goal(
        id="rose",
        want="help a rose bloom for the feast",
        attempt="rush the bloom with a spell",
        lesson="gentle care helps magic last",
        fix="slow down and tend the petals one by one",
        magic_word="bloom",
        consequence="the rose opened like a small red lantern",
        tags={"flower", "lesson", "magic", "ease"},
    ),
}

CHARMS = {
    "ribbon_spellbook": Charm(
        id="ribbon_spellbook",
        label="a silver ribbon spellbook",
        phrase="a silver ribbon spellbook with tiny star marks",
        helps={"magic"},
        eases={"lesson", "category"},
        solution="the right spell was waiting inside it",
    ),
    "lantern_charm": Charm(
        id="lantern_charm",
        label="a lantern charm",
        phrase="a warm lantern charm that glowed like honey",
        helps={"dark"},
        eases={"fear"},
        solution="its glow made the path feel safe",
    ),
    "kindness_bell": Charm(
        id="kindness_bell",
        label="a kindness bell",
        phrase="a small bell that rang like a soft laugh",
        helps={"sharing", "help"},
        eases={"rush"},
        solution="its ring reminded everyone to pause and listen",
    ),
}


@dataclass
class StoryParams:
    goal: str
    charm: str
    name: str
    companion: str
    seed: Optional[int] = None
    params: object | None = None
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small fairy-tale storyworld about magic, ease, and a lesson learned."
    )
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=["fairy", "owl", "mouse"], default=None)
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
    goal = getattr(args, "goal", None) or rng.choice(list(GOALS))
    charm = getattr(args, "charm", None) or rng.choice(list(CHARMS))
    name = getattr(args, "name", None) or rng.choice(["Ada", "Mira", "Nell", "Ivy", "Luna"])
    companion = getattr(args, "companion", None) or rng.choice(["fairy", "owl", "mouse"])
    if goal == "rose" and companion == "mouse":
        # A mouse can still appear, but the tale should stay elegant and plausible.
        companion = rng.choice(["fairy", "owl"])
    return StoryParams(goal=goal, charm=charm, name=name, companion=companion)


def reasonableness_gate(params: StoryParams) -> None:
    goal = _safe_lookup(GOALS, params.goal)
    charm = _safe_lookup(CHARMS, params.charm)
    if "magic" not in charm.helps and "magic" in goal.tags:
        pass
    if params.goal == "brook" and params.companion == "mouse":
        # still valid, but the story needs a helper that can explain the lesson cleanly
        pass


def narrate_setup(world: World, hero: Entity, companion: Entity, goal: Goal, charm: Charm) -> None:
    world.say(
        f"Once upon a time, {hero.id} lived by {world.setting.place}, where {world.setting.detail}"
    )
    world.say(
        f"{hero.id} loved the quiet, but {hero.pronoun('subject')} wanted to {goal.want}, "
        f"and {hero.pronoun('subject')} carried {charm.phrase} wherever {hero.pronoun('subject')} went."
    )
    world.say(
        f"One evening, a {companion.type} friend came close and whispered that the brook looked tired."
    )


def attempt_magic(world: World, hero: Entity, goal: Goal, charm: Charm) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    hero.memes["rush"] = hero.memes.get("rush", 0.0) + 1
    world.say(
        f"{hero.id} decided to {goal.attempt}, and {hero.pronoun('subject')} opened {charm.label} at once."
    )
    world.say(
        f"{hero.id} tried to say the magic word, \"{goal.magic_word}!\""
    )
    world.say(
        f"But because {hero.id} was rushing, the spell only half-worked, and {goal.consequence}."
    )


def lesson_turn(world: World, hero: Entity, companion: Entity, goal: Goal, charm: Charm) -> None:
    hero.memes["sad"] = hero.memes.get("sad", 0.0) + 1
    hero.memes["listen"] = hero.memes.get("listen", 0.0) + 1
    world.say(
        f"{companion.id} did not laugh. Instead, {companion.pronoun('subject')} said, "
        f'\"The best magic is easier when you slow down and ask kindly.\"'
    )
    world.say(
        f"{hero.id} looked at the tangled reeds and understood the lesson: {goal.lesson}."
    )
    world.say(
        f"So {hero.id} stopped, took a breath, and chose to {goal.fix}."
    )
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1


def resolve(world: World, hero: Entity, companion: Entity, goal: Goal, charm: Charm) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    world.say(
        f"Together, {hero.id} and the {companion.type} used {charm.label}, and {goal.consequence}."
    )
    world.say(
        f"The brook shivered, then shone, as if it were smiling under the stars."
    )
    world.say(
        f"{hero.id} tucked {(getattr(charm, 'it')() if callable(getattr(charm, 'it', None)) else getattr(charm, 'it', 'it'))} away and went home with a happy heart, because {goal.lesson}."
    )


def tell(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = World(SETTING)
    goal = _safe_lookup(GOALS, params.goal)
    charm_def = _safe_lookup(CHARMS, params.charm)

    hero = world.add(Entity(id=params.name, kind="character", type="girl"))
    companion = world.add(Entity(id="Companion", kind="character", type=params.companion))
    charm = world.add(
        Entity(
            id=charm_def.id,
            type="thing",
            label=charm_def.label,
            phrase=charm_def.phrase,
            owner=hero.id,
            magical=True,
            plural=charm_def.plural,
        )
    )

    narrate_setup(world, hero, companion, goal, charm_def)
    world.para()
    attempt_magic(world, hero, goal, charm_def)
    world.para()
    lesson_turn(world, hero, companion, goal, charm_def)
    world.para()
    resolve(world, hero, companion, goal, charm_def)

    world.facts.update(
        hero=hero,
        companion=companion,
        charm=charm,
        goal=goal,
        charm_def=charm_def,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short fairy tale about category and ease, with a magical lesson learned.',
        f"Tell a gentle story where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").id} tries to {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "goal").attempt} but learns to slow down.",
        f"Write a happy-ending tale with {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "charm_def").label} and a kind companion who helps the hero understand the lesson.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    companion = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "companion")
    goal = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "goal")
    charm = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "charm_def")
    return [
        QAItem(
            question=f"What did {hero.id} want to do by the willow brook?",
            answer=f"{hero.id} wanted to {goal.want}.",
        ),
        QAItem(
            question=f"What went wrong when {hero.id} rushed the magic spell?",
            answer=f"The spell only half-worked, and {goal.consequence}.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn from the {companion.type} friend?",
            answer=f"{hero.id} learned that {goal.lesson}.",
        ),
        QAItem(
            question=f"How did the story end after {hero.id} used {charm.label} kindly?",
            answer=f"It ended happily, with {goal.consequence} and {hero.id} going home smiling.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fairy tale?",
            answer="A fairy tale is a make-believe story with magic, wonder, and a lesson or happy ending.",
        ),
        QAItem(
            question="What does ease mean?",
            answer="Ease means something feels less hard, lighter, or simpler to do.",
        ),
        QAItem(
            question="Why can a kind helper make magic easier?",
            answer="A kind helper can slow things down, point out a better way, and make a hard job feel smaller.",
        ),
        QAItem(
            question="Why do stories often include a lesson learned?",
            answer="Stories include a lesson learned so readers can see how a character grows and makes better choices.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        parts = []
        if e.label:
            parts.append(f"label={e.label}")
        if e.phrase:
            parts.append(f"phrase={e.phrase}")
        if e.owner:
            parts.append(f"owner={e.owner}")
        if e.magical:
            parts.append("magical=True")
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) " + " ".join(parts))
    return "\n".join(lines)


ASP_RULES = r"""
% Declarative twin for the reasonableness gate.
goal(G) :- goal_name(G).
charm(C) :- charm_name(C).

helps(C, magic) :- charm_helps(C, magic).
eases(C, category) :- charm_eases(C, category).
eases(C, lesson) :- charm_eases(C, lesson).

reasonable(C, G) :- goal(G), charm(C), goal_tag(G, magic), helps(C, magic).
reasonable(C, G) :- goal(G), charm(C), goal_tag(G, lesson), eases(C, lesson).

#show reasonable/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for gid, goal in GOALS.items():
        lines.append(asp.fact("goal_name", gid))
        for tag in sorted(goal.tags):
            lines.append(asp.fact("goal_tag", gid, tag))
    for cid, charm in CHARMS.items():
        lines.append(asp.fact("charm_name", cid))
        for h in sorted(charm.helps):
            lines.append(asp.fact("charm_helps", cid, h))
        for e in sorted(charm.eases):
            lines.append(asp.fact("charm_eases", cid, e))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/2."))
    return sorted(set(asp.atoms(model, "reasonable")))


def valid_pairs() -> list[tuple[str, str]]:
    out = []
    for gid, goal in GOALS.items():
        for cid, charm in CHARMS.items():
            if "magic" in goal.tags and "magic" in charm.helps:
                out.append((gid, cid))
            elif "lesson" in goal.tags and "lesson" in charm.easess:
                out.append((gid, cid))
    return out


def asp_verify() -> int:
    py = set(valid_pairs())
    cl = set(asp_reasonable_pairs())
    if py == cl:
        print(f"OK: clingo gate matches python ({len(py)} pairs).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


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
    StoryParams(goal="brook", charm="ribbon_spellbook", name="Ada", companion="fairy"),
    StoryParams(goal="rose", charm="kindness_bell", name="Mira", companion="owl"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def resolve_pairs(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        goal=getattr(args, "goal", None) or rng.choice(list(GOALS)),
        charm=getattr(args, "charm", None) or rng.choice(list(CHARMS)),
        name=getattr(args, "name", None) or rng.choice(["Ada", "Mira", "Nell", "Ivy", "Luna"]),
        companion=getattr(args, "companion", None) or rng.choice(["fairy", "owl", "mouse"]),
    )
    reasonableness_gate(params)
    return params


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show reasonable/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show reasonable/2."))
        pairs = asp.atoms(model, "reasonable")
        print(f"{len(pairs)} reasonable goal/charm pairs:")
        for g, c in sorted(set(pairs)):
            print(f"  {g:8} {c}")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.goal} with {p.charm}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
