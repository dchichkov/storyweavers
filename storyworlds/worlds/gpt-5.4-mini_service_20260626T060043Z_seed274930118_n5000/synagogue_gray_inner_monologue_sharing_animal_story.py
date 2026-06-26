#!/usr/bin/env python3
"""
A small animal story world about a gray animal at a synagogue, with inner
monologue and sharing as the core turn.
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
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    shared_with: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    stone: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "rabbit", "cat", "dog", "bear"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Place:
    name: str
    quiet: bool = True
    has_bench: bool = True
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


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    kind: str
    value: str = "special"
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
class StoryParams:
    place: str = ""
    hero: str = ""
    friend: str = ""
    treasure: str = ""
    seed: Optional[int] = None
    friend_name: object | None = None
    friend_type: object | None = None
    hero_name: object | None = None
    hero_type: object | None = None
    trait: object | None = None
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


PLACES = {
    "synagogue": Place(name="the synagogue", quiet=True, has_bench=True),
}

HEROES = [
    ("Milo", "mouse"),
    ("Ruby", "rabbit"),
    ("Nori", "cat"),
    ("Toby", "dog"),
    ("Luna", "bear"),
]

FRIENDS = [
    ("Pip", "mouse"),
    ("Hazel", "rabbit"),
    ("Tessa", "cat"),
    ("Benji", "dog"),
    ("Mara", "bear"),
]

TREASURES = {
    "gray_stone": Treasure(
        id="gray_stone",
        label="gray stone",
        phrase="a smooth gray stone",
        kind="stone",
    ),
    "gray_scarf": Treasure(
        id="gray_scarf",
        label="gray scarf",
        phrase="a soft gray scarf",
        kind="scarf",
    ),
    "gray_book": Treasure(
        id="gray_book",
        label="gray book",
        phrase="a little gray book",
        kind="book",
    ),
}

TRAITS = ["curious", "gentle", "shy", "thoughtful", "small", "patient"]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


def _intro(world: World, hero: Entity, trait: str) -> None:
    world.say(f"{hero.id} was a little {trait} {hero.type} who liked quiet places.")


def _setting(world: World) -> None:
    world.say(f"One afternoon, {world.place.name} was calm and still.")


def _inner_monologue(world: World, hero: Entity, treasure: Entity) -> None:
    hero.memes["worry"] = 1.0
    hero.memes["want"] = 1.0
    world.say(
        f"{hero.id} looked at {treasure.label} and thought, "
        f'"I want to keep {(getattr(treasure, 'it')() if callable(getattr(treasure, 'it', None)) else getattr(treasure, 'it', 'it'))} safe, but maybe someone else needs {(getattr(treasure, 'it')() if callable(getattr(treasure, 'it', None)) else getattr(treasure, 'it', 'it'))} too."'
    )


def _meet_friend(world: World, hero: Entity, friend: Entity, treasure: Entity) -> None:
    world.say(
        f"Then {friend.id} came close and smiled at the {treasure.label}. "
        f"{friend.id} had been searching for something small and gray."
    )


def _sharing_turn(world: World, hero: Entity, friend: Entity, treasure: Entity) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1.0
    treasure.shared_with.append(friend.id)
    world.say(
        f"{hero.id} took a breath and shared the {treasure.label}. "
        f"{hero.id} let {friend.id} hold {(getattr(treasure, 'it')() if callable(getattr(treasure, 'it', None)) else getattr(treasure, 'it', 'it'))} for a little while."
    )
    world.say(
        f"{friend.id} held {(getattr(treasure, 'it')() if callable(getattr(treasure, 'it', None)) else getattr(treasure, 'it', 'it'))} gently, and both animals felt warm inside."
    )


def _ending(world: World, hero: Entity, friend: Entity, treasure: Entity) -> None:
    world.say(
        f"When the sun slipped lower, {hero.id} and {friend.id} sat together at the bench, "
        f"watching the gray shine of {treasure.label} in the quiet room."
    )
    world.say(
        f"{hero.id} learned that sharing could make a small thing feel even better."
    )


def tell(place: Place, hero_name: str, hero_type: str, friend_name: str, friend_type: str,
         treasure: Treasure, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type))
    stone = world.add(Entity(id=treasure.id, type=treasure.kind, label=treasure.label, phrase=treasure.phrase))

    _intro(world, hero, trait)
    _setting(world)
    world.say(f"{hero.id} found {stone.phrase} near a quiet bench.")
    _inner_monologue(world, hero, stone)
    _meet_friend(world, hero, friend, stone)
    _sharing_turn(world, hero, friend, stone)
    _ending(world, hero, friend, stone)

    world.facts = {
        "hero": hero,
        "friend": friend,
        "treasure": stone,
        "trait": trait,
        "place": place,
    }
    return world


@dataclass
class StoryConfig:
    place: str
    treasure: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    trait: str
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
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    friend = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "friend")
    treasure = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "treasure")
    return [
        f"Write a gentle animal story set at a synagogue about {hero.id} and {friend.id} sharing {treasure.label}.",
        f"Tell a short story where a {hero.type} named {hero.id} thinks to itself and then shares a gray treasure with {friend.id}.",
        f"Write an animal story with inner monologue and sharing in a quiet synagogue scene.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    friend = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "friend")
    treasure = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "treasure")
    place = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place").name
    trait = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "trait")
    return [
        QAItem(
            question=f"Where did {hero.id} find the {treasure.label}?",
            answer=f"{hero.id} found the {treasure.label} at {place}, near a quiet bench.",
        ),
        QAItem(
            question=f"What did {hero.id} think about before sharing?",
            answer=f"{hero.id} thought about keeping the {treasure.label} safe, and also about whether someone else might need it.",
        ),
        QAItem(
            question=f"What did {hero.id} do for {friend.id}?",
            answer=f"{hero.id} shared the {treasure.label} and let {friend.id} hold it for a little while.",
        ),
        QAItem(
            question=f"How did {hero.id} act in the story?",
            answer=f"{hero.id} was a {trait} animal who chose kindness and sharing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a synagogue?",
            answer="A synagogue is a place where Jewish people gather to pray, learn, and be together.",
        ),
        QAItem(
            question="What does it mean to share?",
            answer="To share means to let someone else use, hold, or enjoy something too.",
        ),
        QAItem(
            question="What does gray look like?",
            answer="Gray is a color that sits between black and white. It can look soft, calm, and quiet.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for p in sample.prompts:
        parts.append(p)
    parts.append("== Story QA ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("== World QA ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


ASP_RULES = r"""
place(synagogue).
color(gray).
theme(inner_monologue).
theme(sharing).

valid_story(P, C, T) :- place(P), color(C), theme(inner_monologue), theme(sharing), treasure(T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("place", "synagogue"), asp.fact("color", "gray"), asp.fact("theme", "inner_monologue"), asp.fact("theme", "sharing"), asp.fact("treasure", "gray_stone"), asp.fact("treasure", "gray_scarf"), asp.fact("treasure", "gray_book")]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    atoms = set(asp.atoms(model, "valid_story"))
    expected = {("synagogue", "gray", "gray_stone"), ("synagogue", "gray", "gray_scarf"), ("synagogue", "gray", "gray_book")}
    if atoms == expected:
        print(f"OK: ASP parity matches ({len(atoms)} stories).")
        return 0
    print("MISMATCH between ASP and Python expectations:")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with synagogue, gray, inner monologue, and sharing.")
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--treasure", choices=list(TREASURES))
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--trait", choices=TRAITS)
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
    place = getattr(args, "place", None) or "synagogue"
    treasure = getattr(args, "treasure", None) or rng.choice(list(TREASURES))
    hero_name, hero_type = rng.choice(HEROES)
    friend_name, friend_type = rng.choice(FRIENDS)
    if getattr(args, "name", None):
        hero_name = getattr(args, "name", None)
    if getattr(args, "friend", None):
        friend_name = getattr(args, "friend", None)
    if getattr(args, "trait", None):
        trait = getattr(args, "trait", None)
    else:
        trait = rng.choice(TRAITS)
    return StoryParams(place=place, treasure=treasure, hero_name=hero_name, hero_type=hero_type,
                       friend_name=friend_name, friend_type=friend_type, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(PLACES, params.place),
        params.hero_name,
        params.hero_type,
        params.friend_name,
        params.friend_type,
        _safe_lookup(TREASURES, params.treasure),
        params.trait,
    )
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.shared_with:
            bits.append(f"shared_with={e.shared_with}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        combos = [
            StoryParams("synagogue", "gray_stone", "Milo", "mouse", "Pip", "mouse", "curious"),
            StoryParams("synagogue", "gray_scarf", "Ruby", "rabbit", "Hazel", "rabbit", "gentle"),
            StoryParams("synagogue", "gray_book", "Nori", "cat", "Tessa", "cat", "thoughtful"),
        ]
        samples = [generate(p) for p in combos]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
