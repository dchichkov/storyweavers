#!/usr/bin/env python3
"""
A standalone storyworld for a small comedic domain about sound effects,
bravery, and surprise.

Seed premise:
- A prankster tries to instigate a dramatic sound effect.
- A timid character gets a little frightened, then gets brave.
- A surprise reveal flips the moment into a laugh.

This world models:
- typed entities with physical meters and emotional memes
- state-driven causality: sound, startle, bravery, relief, laughter
- a simple compromise/resolution where the sound is revealed to be harmless

The included seed words are represented through the world vocabulary:
- instigate
- meyme
- skin

The story style is child-facing, concrete, and comedic.
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
# Parameters and registries
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
class Setting:
    place: str
    indoors: bool
    surfaces: list[str]
    sound_rich: bool = True
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
class SoundEffect:
    id: str
    name: str
    onomatopoeia: str
    trigger: str
    volume: int
    surprise_level: int
    safe: bool
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
class Prop:
    id: str
    label: str
    phrase: str
    type: str
    role: str  # "prank", "cover", "reveal", "comfort"
    affects: set[str] = field(default_factory=set)
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


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoors=True, surfaces=["table", "floor", "stool"]),
    "backyard": Setting(place="the backyard", indoors=False, surfaces=["grass", "bench", "fence"]),
    "playroom": Setting(place="the playroom", indoors=True, surfaces=["rug", "couch", "box"]),
    "garage": Setting(place="the garage", indoors=True, surfaces=["toolbench", "cart", "door"]),
}

SOUND_EFFECTS = {
    "boing": SoundEffect(
        id="boing",
        name="a rubbery boing",
        onomatopoeia="Boing!",
        trigger="pushed the springy toy",
        volume=3,
        surprise_level=2,
        safe=True,
        tags={"sound", "bounce", "funny"},
    ),
    "pop": SoundEffect(
        id="pop",
        name="a loud pop",
        onomatopoeia="POP!",
        trigger="squeezed the balloon too hard",
        volume=5,
        surprise_level=4,
        safe=True,
        tags={"sound", "surprise", "balloon"},
    ),
    "clang": SoundEffect(
        id="clang",
        name="a clanging crash",
        onomatopoeia="CLANG!",
        trigger="banged the spoon on the pan",
        volume=6,
        surprise_level=5,
        safe=True,
        tags={"sound", "metal", "loud"},
    ),
    "whoosh": SoundEffect(
        id="whoosh",
        name="a spooky whoosh",
        onomatopoeia="Whooooosh!",
        trigger="pulled the curtain aside",
        volume=4,
        surprise_level=3,
        safe=True,
        tags={"sound", "wind", "trick"},
    ),
}

PROPS = {
    "toy": Prop(
        id="toy",
        label="spring toy",
        phrase="a springy toy with a silly face",
        type="toy",
        role="prank",
        affects={"boing"},
    ),
    "balloon": Prop(
        id="balloon",
        label="balloon",
        phrase="a big round balloon",
        type="balloon",
        role="prank",
        affects={"pop"},
    ),
    "pan": Prop(
        id="pan",
        label="pan",
        phrase="a shiny pan",
        type="pan",
        role="prank",
        affects={"clang"},
    ),
    "curtain": Prop(
        id="curtain",
        label="curtain",
        phrase="a long curtain",
        type="curtain",
        role="prank",
        affects={"whoosh"},
    ),
    "gloves": Prop(
        id="gloves",
        label="gloves",
        phrase="a pair of bright oven gloves",
        type="gloves",
        role="cover",
        affects={"skin"},
    ),
    "mask": Prop(
        id="mask",
        label="mask",
        phrase="a paper mask with a grin",
        type="mask",
        role="reveal",
        affects={"surprise"},
    ),
    "badge": Prop(
        id="badge",
        label="bravery badge",
        phrase="a little bravery badge",
        type="badge",
        role="comfort",
        affects={"bravery"},
    ),
}

CHARACTER_NAMES = ["Milo", "Nina", "Toby", "Zara", "Penny", "Jules", "Ravi", "Luna"]
CHARACTER_TYPES = ["boy", "girl"]
TRAITS = ["curious", "shy", "lively", "silly", "careful", "bright"]


# ---------------------------------------------------------------------------
# Story model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    prank: object | None = None
    reveal: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def ref(self) -> str:
        return self.label or self.id
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
class StoryParams:
    setting: str
    sound: str
    prank_prop: str
    reveal_prop: str
    name: str
    gender: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


def _startle(world: World, target: Entity, sound: SoundEffect) -> None:
    if target.memes.get("startle", 0) >= THRESHOLD:
        return
    target.memes["startle"] = 1.0
    target.memes["surprise"] = target.memes.get("surprise", 0) + sound.surprise_level / 2
    target.memes["skin_crawl"] = target.memes.get("skin_crawl", 0) + 1.0
    world.say(f"{sound.onomatopoeia} made {target.id}'s skin feel all tingly.")


def _brave_up(world: World, hero: Entity, helper: Entity) -> None:
    if hero.memes.get("startle", 0) < THRESHOLD:
        return
    sig = ("brave_up", hero.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1.0
    hero.memes["fear"] = 0.0
    world.say(f"{hero.id} took a breath and tried to act brave.")


def _laugh(world: World, hero: Entity, helper: Entity, sound: SoundEffect) -> None:
    sig = ("laugh", hero.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1.0
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1.0
    world.say(
        f"Then they saw it was only a funny little trick, and both of them laughed."
    )


def predict_startle(world: World, sound: SoundEffect) -> bool:
    sim = world.copy()
    hero = sim.get(sim.facts["hero"].id)
    _startle(sim, hero, sound)
    return hero.memes.get("startle", 0) >= THRESHOLD


def tell(setting: Setting, sound: SoundEffect, prank_prop: Prop, reveal_prop: Prop,
         hero_name: str, gender: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender))
    helper = world.add(Entity(id="Helper", kind="character", type="friend", label="a friend"))
    prank = world.add(Entity(id=prank_prop.id, kind="thing", type=prank_prop.type,
                             label=prank_prop.label, phrase=prank_prop.phrase))
    reveal = world.add(Entity(id=reveal_prop.id, kind="thing", type=reveal_prop.type,
                              label=reveal_prop.label, phrase=reveal_prop.phrase))

    hero.memes["curiosity"] = 1.0
    hero.memes["fear"] = 0.0
    helper.memes["mischief"] = 1.0

    world.facts.update(hero=hero, helper=helper, prank=prank, reveal=reveal,
                       sound=sound, trait=trait)

    # Act 1: setup
    world.say(
        f"{hero.id} was a {trait} {gender} who liked quiet days and funny surprises."
    )
    world.say(
        f"{helper.label} said they had an idea to instigate {sound.name}."
    )
    world.say(
        f"They pointed at {prank.phrase} and grinned."
    )

    # Act 2: the noise
    world.para()
    world.say(f"In {setting.place}, {helper.id} {sound.trigger}.")
    world.say(sound.onomatopoeia)
    _startle(world, hero, sound)

    if predict_startle(world, sound):
        world.say(
            f"{hero.id} blinked and hugged {hero.pronoun('possessive')} own sides like a tiny turtle."
        )

    # Act 2b: bravery
    _brave_up(world, hero, helper)
    world.say(
        f"{hero.id} peeped, then stood up straighter, trying hard to be brave."
    )

    # Act 3: surprise reveal
    world.para()
    world.say(
        f"Then {helper.id} lifted the cloth and showed {reveal.phrase}."
    )
    _laugh(world, hero, helper, sound)
    world.say(
        f"It was not a monster at all, just a silly surprise, and {hero.id}'s skin stopped tingling."
    )

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    sound: SoundEffect = _safe_fact(world, f, "sound")
    return [
        f'Write a short comedy story for children that includes the word "instigate" and the sound "{sound.onomatopoeia}".',
        f"Tell a playful story where {hero.id} gets startled, then shows bravery, and a surprise turns the scare into laughter.",
        f"Write a small story about a noisy prank, a brave kid, and a harmless reveal in {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    sound: SoundEffect = _safe_fact(world, f, "sound")
    trait: str = _safe_fact(world, f, "trait")

    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a {trait} {hero.type}, and {helper.label}, who tried to instigate a funny sound effect.",
        ),
        QAItem(
            question=f"What sound did the helper make?",
            answer=f"The helper made {sound.name}, and the story said {sound.onomatopoeia}.",
        ),
        QAItem(
            question=f"How did {hero.id} feel after the loud surprise?",
            answer=f"{hero.id} felt startled at first, then grew brave, and finally laughed when the surprise turned out to be harmless.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a made-up or added noise that helps make a scene feel funny, exciting, or dramatic.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when you feel a little scared.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that makes you blink, gasp, or smile.",
        ),
        QAItem(
            question="What is skin?",
            answer="Skin is the soft covering on the outside of your body.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label!r}")
        out.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A sound can startle a character if it is loud enough.
startled(H,S) :- hero(H), sound(S), volume(S,V), V >= 4.

% Bravery follows startle when the hero chooses to be brave.
brave(H) :- startled(H,S), hero(H), sound(S).

% The reveal is a harmless surprise when the prop is a reveal prop.
surprise_reveal(P) :- prop(P), role(P,reveal).

% A story is valid when the sound, bravery, and surprise are all present.
valid_story(SP,PP,RP) :- sound(SP), prop(PP), prop(RP),
                         role(PP,prank), role(RP,reveal),
                         sound_tag(SP,sound), surprise_reveal(RP).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        if s.sound_rich:
            lines.append(asp.fact("sound_rich", sid))
    for sid, s in SOUND_EFFECTS.items():
        lines.append(asp.fact("sound", sid))
        lines.append(asp.fact("volume", sid, s.volume))
        lines.append(asp.fact("surprise_level", sid, s.surprise_level))
        for t in sorted(s.tags):
            lines.append(asp.fact("sound_tag", sid, t))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        lines.append(asp.fact("role", pid, p.role))
        for a in sorted(p.affects):
            lines.append(asp.fact("affects", pid, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set()
    for sid in SOUND_EFFECTS:
        for pp in PROPS:
            for rp in PROPS:
                if _safe_lookup(PROPS, pp).role == "prank" and _safe_lookup(PROPS, rp).role == "reveal":
                    py_set.add((sid, pp, rp))
    if asp_set == py_set:
        print(f"OK: clingo parity check passed ({len(asp_set)} tuples).")
        return 0
    print("MISMATCH between ASP and Python sets.")
    print("only in ASP:", sorted(asp_set - py_set))
    print("only in Python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Resolve / generate / emit
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="kitchen", sound="clang", prank_prop="pan", reveal_prop="mask", name="Milo", gender="boy", trait="shy"),
    StoryParams(setting="playroom", sound="pop", prank_prop="balloon", reveal_prop="badge", name="Nina", gender="girl", trait="curious"),
    StoryParams(setting="backyard", sound="boing", prank_prop="toy", reveal_prop="mask", name="Toby", gender="boy", trait="lively"),
    StoryParams(setting="garage", sound="whoosh", prank_prop="curtain", reveal_prop="badge", name="Zara", gender="girl", trait="careful"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld: sound effects, bravery, and surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--sound", choices=SOUND_EFFECTS)
    ap.add_argument("--prank-prop", choices=PROPS)
    ap.add_argument("--reveal-prop", choices=[k for k, v in PROPS.items() if v.role == "reveal"])
    ap.add_argument("--name", choices=CHARACTER_NAMES)
    ap.add_argument("--gender", choices=CHARACTER_TYPES)
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
    setting_id = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    sound_id = getattr(args, "sound", None) or rng.choice(list(SOUND_EFFECTS))
    prank_id = getattr(args, "prank_prop", None) or rng.choice([k for k, v in PROPS.items() if v.role == "prank"])
    reveal_id = getattr(args, "reveal_prop", None) or rng.choice([k for k, v in PROPS.items() if v.role == "reveal"])
    if prank_id == reveal_id:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    sound = _safe_lookup(SOUND_EFFECTS, sound_id)
    prank = _safe_lookup(PROPS, prank_id)
    reveal = _safe_lookup(PROPS, reveal_id)
    if sound_id not in prank.affects:
        # keep the story grounded: a prank prop should plausibly make the sound
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(CHARACTER_NAMES)
    gender = getattr(args, "gender", None) or rng.choice(CHARACTER_TYPES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting_id, sound=sound_id, prank_prop=prank_id, reveal_prop=reveal_id,
                       name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(SOUND_EFFECTS, params.sound),
        _safe_lookup(PROPS, params.prank_prop),
        _safe_lookup(PROPS, params.reveal_prop),
        params.name,
        params.gender,
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(f"{len(asp.atoms(model, 'valid_story'))} compatible story tuples.")
        for t in sorted(set(asp.atoms(model, "valid_story"))):
            print("  ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
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
            header = f"### {p.name}: {p.sound} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
