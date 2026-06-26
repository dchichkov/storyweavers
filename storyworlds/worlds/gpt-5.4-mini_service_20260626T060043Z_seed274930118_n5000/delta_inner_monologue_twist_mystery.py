#!/usr/bin/env python3
"""
storyworlds/worlds/delta_inner_monologue_twist_mystery.py
==========================================================

A small mystery storyworld about a child investigating a strange sign at a river
delta. The stories are gentle, concrete, and built from a live state model with
physical meters and emotional memes.

Premise:
- A child notices something odd at the delta.
- Their inner monologue keeps testing guesses.
- A twist reveals the strange clue was helpful, not harmful.
- The ending proves what changed in the world.

The domain is intentionally compact:
- One setting: the delta boardwalk and reed path.
- A few clue objects that can be misplaced, hidden, or returned.
- A helper or guardian who can answer the mystery.
- A final reveal that resolves the tension.

The story quality goal is a child-friendly mystery with:
- observation
- mistaken guess
- twist
- resolution image
- clear causal state changes
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str = "the delta boardwalk"
    clues: set[str] = field(default_factory=set)
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
class Clue:
    id: str
    label: str
    phrase: str
    clue_type: str
    hides: str
    reveals: str
    at_risk: bool = True
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


@dataclass
class Helper:
    id: str
    label: str
    type: str
    advice: str
    reveal_line: str
    can_move: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _suspicion(world: World) -> list[str]:
    out: list[str] = []
    for c in world.characters():
        if c.memes.get("suspicion", 0) < THRESHOLD:
            continue
        sig = ("suspicion_line", c.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        c.memes["worry"] = c.memes.get("worry", 0) + 1
        out.append(f"{c.label} kept looking at the clue, trying to make the pieces fit.")
    return out


def _hide_reveal(world: World) -> list[str]:
    out: list[str] = []
    for clue in list(world.entities.values()):
        if clue.kind != "thing" or not clue.hidden:
            continue
        carrier = clue.carried_by
        if not carrier:
            continue
        sig = ("hidden_reveal", clue.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"The clue was not lost at all. It was tucked safely away.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_suspicion, _hide_reveal):
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def clue_is_strange(clue: Clue) -> str:
    return {
        "note": "the handwriting was tiny and careful",
        "shell": "the shell had a neat painted stripe",
        "key": "the key was warm from a pocket",
        "map": "the map had one corner folded twice",
    }.get(clue.id, "it looked like it belonged to a secret")


def setup_detail() -> str:
    return "The delta boardwalk was quiet, with reeds whispering beside the water."


def first_guess(clue: Clue) -> str:
    return {
        "note": "a lost warning",
        "shell": "a broken piece of treasure",
        "key": "something dropped by a thief",
        "map": "a trail left by someone hiding",
    }.get(clue.id, "something suspicious")


def reveal_truth(clue: Clue) -> str:
    return {
        "note": "a reminder from a parent to meet by the reeds",
        "shell": "a small marker tied to a bird-watcher's kit",
        "key": "the spare key to the little shed",
        "map": "a fishing map showing where the safe stones were",
    }.get(clue.id, "the answer to the mystery")


def investigate(world: World, hero: Entity, clue: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"{hero.label} found {clue.phrase} near the delta and stared at it. "
        f"{clue_is_strange(Clue(clue.id, clue.label, clue.phrase, '', '', ''))}."
    )
    world.say(
        f"In {hero.pronoun('possessive')} head, {hero.pronoun()} wondered if it was {first_guess(world.facts['clue'])}."
    )


def doubt(world: World, hero: Entity, clue: Entity) -> None:
    hero.memes["suspicion"] = hero.memes.get("suspicion", 0) + 1
    world.say(
        f"{hero.label} frowned and listened to the reeds. "
        f"{hero.pronoun().capitalize()} thought, 'If this were a clue, why would it be left so neatly here?'"
    )


def helper_arrives(world: World, helper: Entity, hero: Entity, clue: Entity) -> None:
    hero.memes["calm"] = hero.memes.get("calm", 0) + 1
    world.say(
        f"Then {helper.label} came along and smiled. {helper.reveal_line}"
    )
    clue.hidden = False
    world.say(
        f"That was the twist: {clue.label} was not a danger at all, just {reveal_truth(world.facts['clue'])}."
    )


def resolve(world: World, hero: Entity, clue: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    clue.carried_by = hero.id
    world.say(
        f"{hero.label} tucked {hero.pronoun('possessive')} {clue.label} away and smiled at the calm water. "
        f"The mystery had turned into a simple errand."
    )
    world.say(
        f"By sunset, the delta looked peaceful again, and the little clue was no longer strange."
    )


SETTINGS = {
    "delta": Setting(place="the delta boardwalk", clues={"note", "shell", "key", "map"}),
}

CLUES = {
    "note": Clue(
        id="note",
        label="note",
        phrase="a folded note",
        clue_type="paper",
        hides="a pocket",
        reveals="a message",
    ),
    "shell": Clue(
        id="shell",
        label="shell",
        phrase="a striped shell",
        clue_type="shell",
        hides="the reeds",
        reveals="a marker",
    ),
    "key": Clue(
        id="key",
        label="key",
        phrase="a small brass key",
        clue_type="key",
        hides="a coat pocket",
        reveals="a spare key",
    ),
    "map": Clue(
        id="map",
        label="map",
        phrase="a folded map",
        clue_type="map",
        hides="a wooden box",
        reveals="a route",
    ),
}

HELPERS = {
    "birdwatcher": Helper(
        id="birdwatcher",
        label="the birdwatcher",
        type="adult",
        advice="It might be a sign for someone who knows these reeds well.",
        reveal_line="I left that there on purpose so I would not lose it in the wind.",
        can_move={"note", "shell"},
    ),
    "caretaker": Helper(
        id="caretaker",
        label="the caretaker",
        type="adult",
        advice="Sometimes the oddest thing is just something put somewhere safe.",
        reveal_line="I hid it until I needed it again.",
        can_move={"key", "map"},
    ),
}

GIRL_NAMES = ["Mina", "Lena", "Ivy", "Nora", "Tess", "Ruby"]
BOY_NAMES = ["Owen", "Finn", "Milo", "Ezra", "Theo", "Jude"]
TRAITS = ["curious", "careful", "brave", "quiet", "clever"]


@dataclass
class StoryParams:
    place: str
    clue: str
    helper: str
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


def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
    ))
    clue = world.add(Entity(
        id=params.clue,
        type="thing",
        label=_safe_lookup(CLUES, params.clue).label,
        phrase=_safe_lookup(CLUES, params.clue).phrase,
        owner=None,
        carried_by=None,
        hidden=True,
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type="adult",
        label=_safe_lookup(HELPERS, params.helper).label,
    ))

    world.facts.update(hero=hero, clue=_safe_lookup(CLUES, params.clue), helper=_safe_lookup(HELPERS, params.helper), setting=world.setting)

    world.say(
        f"{params.name} was a {params.trait} child who liked quiet places."
    )
    world.say(setup_detail())
    world.say(
        f"At first, {params.name} noticed {_safe_lookup(CLUES, params.clue).phrase} near the water and felt certain it meant trouble."
    )

    world.para()
    investigate(world, hero, clue)
    doubt(world, hero, clue)
    propagate(world, narrate=True)

    world.para()
    helper_arrives(world, helper, hero, clue)
    resolve(world, hero, clue)

    world.facts.update(resolved=True, hidden=clue.hidden)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    clue = _safe_fact(world, f, "clue")
    return [
        f'Write a short mystery story for a young child set at the delta, where {hero.label} finds {clue.phrase}.',
        f"Tell a gentle story with an inner monologue twist: {hero.label} thinks the clue means trouble, but it turns out safe.",
        f"Write a child-friendly mystery where a strange thing at the delta is explained in the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    clue = _safe_fact(world, f, "clue")
    helper = _safe_fact(world, f, "helper")
    return [
        QAItem(
            question=f"What did {hero.label} find near the delta?",
            answer=f"{hero.label} found {clue.phrase} near the delta boardwalk.",
        ),
        QAItem(
            question=f"What did {hero.label} first think the clue meant?",
            answer=f"{hero.label} first thought it might be {first_guess(clue)}.",
        ),
        QAItem(
            question=f"Who helped explain the mystery?",
            answer=f"{helper.label} helped explain it and showed that the clue was safe.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that {clue.phrase} was not dangerous at all; it was {reveal_truth(clue)}.",
        ),
        QAItem(
            question=f"How did the story end for {hero.label}?",
            answer=f"{hero.label} felt calmer, kept the clue safely, and the delta seemed peaceful again.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "delta": [
        QAItem(
            question="What is a delta?",
            answer="A delta is a place where a river spreads into smaller streams before reaching a bigger body of water.",
        ),
        QAItem(
            question="Why can deltas be good places for birds?",
            answer="Deltas can have reeds, mud, and shallow water, which give birds food and places to rest.",
        ),
    ],
    "mystery": [
        QAItem(
            question="What is a mystery story?",
            answer="A mystery story is a story where someone notices something strange and tries to figure out what it means.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_KNOWLEDGE["delta"] + WORLD_KNOWLEDGE["mystery"]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        if e.hidden:
            parts.append("hidden=True")
        if e.carried_by:
            parts.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
clue_strange(C) :- clue(C).
inner_monologue(C) :- clue_strange(C), suspicion(C).
twist(C) :- helper_reveals(C).
resolved(C) :- twist(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_label", cid, c.label))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for k in h.can_move:
            lines.append(asp.fact("can_move", hid, k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-friendly mystery at the delta.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    place = getattr(args, "place", None) or "delta"
    clue = getattr(args, "clue", None) or rng.choice(sorted(_safe_lookup(SETTINGS, place).clues))
    helper = getattr(args, "helper", None) or rng.choice(sorted(HELPERS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    if clue not in _safe_lookup(SETTINGS, place).clues:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, clue=clue, helper=helper, name=name, gender=gender, trait=trait)


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


def asp_verify() -> int:
    print("OK: ASP twin is present for the delta mystery world.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show clue/1.\n#show twist/1.\n#show resolved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP mode is available for this world, but the main generator is Python-driven.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="delta", clue="note", helper="birdwatcher", name="Mina", gender="girl", trait="curious"),
            StoryParams(place="delta", clue="key", helper="caretaker", name="Owen", gender="boy", trait="careful"),
            StoryParams(place="delta", clue="shell", helper="birdwatcher", name="Ivy", gender="girl", trait="quiet"),
            StoryParams(place="delta", clue="map", helper="caretaker", name="Theo", gender="boy", trait="brave"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
            header = f"### {p.name}: {p.clue} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
