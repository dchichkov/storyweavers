#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/thought_pee_war_transformation_animal_story.py
==============================================================================================================

A small animal-story world about a tiny worry, a pee accident, a pretend war,
and a gentle transformation.

Seed image:
- A little animal notices a noisy "war" of clashing voices near a patch of grass.
- It thinks hard about what to do.
- It has to pee.
- The pee waters a magic seed and transforms the moment into peace.

This world keeps the style child-facing and concrete, with a simple simulated
state:
- physical meters: nervousness, puddle, growth, mess, calm, bloom
- emotional memes: thought, fear, courage, kindness, relief, pride

The core story pattern:
1) Setup: a small animal notices an argument and thinks it sounds like war.
2) Tension: the animal gets nervous, needs to pee, and accidentally wets a magic seed patch.
3) Turn: the wet seed transforms into a sprout.
4) Resolution: the sprout's gentle change helps everyone stop the fake war and feel calm.

The world is intentionally narrow: not every animal, place, or event is valid.
Reasonable stories must preserve the causal shape above.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "mouse": {"subject": "it", "object": "it", "possessive": "its"},
            "rabbit": {"subject": "it", "object": "it", "possessive": "its"},
            "fox": {"subject": "it", "object": "it", "possessive": "its"},
            "duck": {"subject": "it", "object": "it", "possessive": "its"},
            "bear": {"subject": "it", "object": "it", "possessive": "its"},
            "hedgehog": {"subject": "it", "object": "it", "possessive": "its"},
            "friend": {"subject": "they", "object": "them", "possessive": "their"},
        }
        return mapping.get(self.type, {"subject": "it", "object": "it", "possessive": "its"})[case]
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
    id: str
    label: str
    afford_transform: bool = False
    afford_argument: bool = False
    afford_pee: bool = False
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
class SeedPatch:
    id: str
    label: str
    state: str = "dry"  # dry -> wet -> sprout -> bloom
    owner: Optional[str] = None
    seed_patch: object | None = None
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
    place: str = ""
    hero: str = ""
    friend: str = ""
    seed_patch: str = ""
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
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.seed_patch = SeedPatch(id="seed", label="a tiny magic seed patch")
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
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


HEROES = {
    "mouse": "mouse",
    "rabbit": "rabbit",
    "fox": "fox",
    "duck": "duck",
    "bear": "bear",
    "hedgehog": "hedgehog",
}

FRIENDS = {
    "mouse": "friend",
    "rabbit": "friend",
    "fox": "friend",
    "duck": "friend",
    "bear": "friend",
    "hedgehog": "friend",
}

PLACES = {
    "meadow": Place("meadow", "the meadow", afford_transform=True, afford_argument=True, afford_pee=True),
    "pond": Place("pond", "the pond", afford_transform=True, afford_argument=True, afford_pee=True),
    "garden": Place("garden", "the garden", afford_transform=True, afford_argument=True, afford_pee=True),
    "hill": Place("hill", "the little hill", afford_transform=True, afford_argument=True, afford_pee=True),
}

CURATED = [
    StoryParams(place="meadow", hero="mouse", friend="rabbit", seed_patch="seed"),
    StoryParams(place="garden", hero="fox", friend="duck", seed_patch="seed"),
    StoryParams(place="pond", hero="hedgehog", friend="bear", seed_patch="seed"),
]

HERO_NAMES = {
    "mouse": ["Milo", "Mimi", "Moss"],
    "rabbit": ["Rina", "Roo", "Riley"],
    "fox": ["Fenn", "Fia", "Foxley"],
    "duck": ["Dottie", "Dew", "Duna"],
    "bear": ["Bram", "Bibi", "Bobo"],
    "hedgehog": ["Hugo", "Hana", "Hush"],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about thought, pee, war, and transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--friend", choices=set(FRIENDS.values()))
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


def valid_story(place: str, hero: str) -> bool:
    return place in PLACES and hero in HEROES


def select_combo(args: argparse.Namespace, rng: random.Random) -> tuple[str, str]:
    combos = [(p, h) for p in PLACES for h in HEROES if valid_story(p, h)]
    combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "hero", None) is None or c[1] == getattr(args, "hero", None))]
    if not combos:
        pass
    return rng.choice(list(combos))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place, hero = select_combo(args, rng)
    friend = getattr(args, "friend", None) or rng.choice(list(FRIENDS.values()))
    return StoryParams(place=place, hero=hero, friend=friend, seed=getattr(args, "seed", None))


def start_story(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"Little {hero.label} lived near {world.place.label}. "
        f"{hero.pronoun().capitalize()} liked quiet days, soft grass, and small safe thoughts."
    )
    world.say(
        f"One afternoon, {hero.label} saw {friend.label} and another animal bumping noses over a shiny leaf. "
        f"{hero.label} thought the noise sounded like a tiny war."
    )


def feel_thought(world: World, hero: Entity) -> None:
    hero.memes["thought"] += 1
    hero.memes["fear"] += 1
    world.say(
        f"{hero.label} thought and thought. "
        f"The more {hero.pronoun('subject')} thought, the wobblier {hero.pronoun('possessive')} tummy felt."
    )


def needs_pee(world: World, hero: Entity) -> None:
    hero.meters["pee"] += 1
    world.say(
        f"Then {hero.label} had to pee right away. "
        f"{hero.pronoun().capitalize()} hurried to the soft dirt beside the seed patch."
    )


def pee_on_seed(world: World, hero: Entity) -> None:
    sig = ("pee_seed", hero.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.meters["pee"] += 1
    world.seed_patch.state = "wet"
    world.seed_patch.owner = hero.id
    hero.meters["mess"] += 1
    world.say(
        f"{hero.label} peed on the little patch by accident. "
        f"The wet spot soaked into the seed and made the ground warm and shiny."
    )


def transform_seed(world: World, hero: Entity) -> None:
    if world.seed_patch.state != "wet":
        return
    world.seed_patch.state = "sprout"
    hero.memes["relief"] += 1
    hero.memes["courage"] += 1
    world.say(
        f"At once, the seed transformed. A tiny green sprout poked up, as bright as a smile."
    )


def stop_war(world: World, hero: Entity, friend: Entity) -> None:
    friend.memes["calm"] += 1
    hero.memes["calm"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"{hero.label} pointed at the sprout and took a deep breath. "
        f'"Maybe we can stop the war and share the leaf," {hero.label} said.'
    )
    world.say(
        f"The animals looked at the sprout, blinked, and went quiet. "
        f"They sat in a little ring instead of fighting."
    )


def bloom_finish(world: World, hero: Entity, friend: Entity) -> None:
    world.seed_patch.state = "bloom"
    world.say(
        f"By the end, the sprout had become a small flower. "
        f"{hero.label} was still a little embarrassed, but also brave, and {friend.label} was smiling beside {hero.pronoun('object')}."
    )
    world.say(
        f"The meadow felt peaceful again, with a flower where the noisy war had been."
    )


def tell(world: World, hero_name: str, hero_type: str, friend_type: str) -> World:
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    friend = world.add(Entity(id="Friend", kind="character", type=friend_type, label="the friend"))

    start_story(world, hero, friend)
    world.para()
    feel_thought(world, hero)
    needs_pee(world, hero)
    pee_on_seed(world, hero)
    transform_seed(world, hero)
    world.para()
    stop_war(world, hero, friend)
    bloom_finish(world, hero, friend)

    world.facts = {
        "hero": hero,
        "friend": friend,
        "place": world.place,
        "seed_patch": world.seed_patch,
    }
    return world


KNOWLEDGE = {
    "thought": [
        ("What is a thought?", "A thought is something your mind makes when you notice, remember, wonder, or plan."),
    ],
    "pee": [
        ("What is pee?", "Pee is liquid waste that animals and people need to let out from their bodies."),
    ],
    "war": [
        ("What is war?", "War is a very serious fight between groups. In a child's story, the word can also mean a pretend or noisy quarrel."),
    ],
    "transform": [
        ("What does transform mean?", "To transform means to change into something different."),
    ],
    "flower": [
        ("What does a flower need to grow?", "A flower usually needs water, light, and good soil to grow well."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    place = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place").label
    return [
        f"Write a short animal story about {hero.label} at {place} that includes the words thought, pee, war, and transform.",
        f"Tell a gentle story where {hero.label} worries, has to pee, and a tiny transformation helps stop a war.",
        f"Write a child-friendly animal tale in which a wet seed changes after a pee accident and everyone becomes calm.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    friend = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "friend")
    place = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place")
    seed_patch = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "seed_patch")

    return [
        QAItem(
            question=f"Where did {hero.label} live?",
            answer=f"{hero.label} lived near {place.label}.",
        ),
        QAItem(
            question=f"What did {hero.label} think the noise sounded like?",
            answer=f"{hero.label} thought the noise sounded like a tiny war.",
        ),
        QAItem(
            question=f"What happened after {hero.label} peed on the seed patch?",
            answer=f"The seed patch got wet and then transformed into a sprout.",
        ),
        QAItem(
            question=f"How did the story end for {hero.label} and {friend.label}?",
            answer="They stopped fighting, shared the leaf, and sat quietly beside a small flower.",
        ),
        QAItem(
            question=f"What did the wet seed become?",
            answer=f"The wet seed became a sprout, and then it bloomed into a small flower.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ["thought", "pee", "war", "transform", "flower"]:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"place={world.place.label}")
    lines.append(f"seed_patch_state={world.seed_patch.state}")
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_type(H).
valid_story(P,H) :- place(P), hero_type(H).

story_event(thought) :- valid_story(P,H), place(P), hero_type(H).
story_event(pee) :- valid_story(P,H), place(P), hero_type(H).
story_event(war) :- valid_story(P,H), place(P), hero_type(H).
story_event(transformation) :- valid_story(P,H), place(P), hero_type(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for hid in HEROES:
        lines.append(asp.fact("hero_type", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = {(p, h) for p in PLACES for h in HEROES if valid_story(p, h)}
    clingo = set(asp_valid_stories())
    if py == clingo:
        print(f"OK: ASP matches Python ({len(py)} stories).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - clingo))
    print("only asp:", sorted(clingo - py))
    return 1


def build_story(params: StoryParams) -> StorySample:
    place = _safe_lookup(PLACES, params.place)
    world = World(place)
    hero_name = random.choice(_safe_lookup(HERO_NAMES, params.hero))
    world = tell(world, hero_name, params.hero, params.friend)
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


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "hero", None) and not valid_story(getattr(args, "place", None), getattr(args, "hero", None)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    hero = getattr(args, "hero", None) or rng.choice(list(HEROES))
    friend = getattr(args, "friend", None) or rng.choice(list(FRIENDS.values()))
    return StoryParams(place=place, hero=hero, friend=friend, seed=getattr(args, "seed", None))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        raise SystemExit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        for p, h in stories[:20]:
            print(p, h)
        print(f"{len(stories)} stories")
        return

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < getattr(args, "n", None) * 20 + 20:
            rng = random.Random(base + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base + i
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

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
