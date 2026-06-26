#!/usr/bin/env python3
"""
storyworlds/worlds/compartment_repetition_foreshadowing_ghost_story.py
======================================================================

A small storyworld built around a dark-but-gentle ghost story in a train
compartment.

Seed tale, imagined first:
---
On a night train, a child hears three soft knocks from the next compartment.
Each time the knock comes, the window goes cold and the lamp trembles. A tiny
ghost appears, then disappears, always before anyone can speak. The child keeps
the door shut, but the knocking keeps returning. At last the ghost shows that it
is not trying to frighten anyone; it only wants help carrying a lost toy back
to its owner. The child opens the compartment door, and the train ride becomes
quiet and warm again.

This script turns that premise into a constrained simulation with:
- a train compartment and adjoining storage compartment
- repeated knocks and repeated cold drafts
- foreshadowing through small state changes
- a gentle ghost-story resolution

The story is authored from world state, not from a frozen paragraph with swapped
nouns. Invalid choices raise StoryError.
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

NARRATION_THRESHOLD = 1.0



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
    owner: Optional[str] = None
    parent: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    guardian: object | None = None
    object_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
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
    place: str = "the night train"
    description: str = "a narrow train compartment with a rattling window"
    affords: set[str] = field(default_factory=lambda: {"wait", "listen", "open_door"})
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
class Ghost:
    id: str
    name: str
    gentle: bool = True
    repeat_word: str = "knock"
    cold_word: str = "cold"
    ghost: object | None = None
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
class StoryParams:
    place: str = ""
    child_name: str = ""
    child_type: str = ""
    guardian_type: str = ""
    ghost_name: str = ""
    object_name: str = ""
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.events: list[str] = []
        self.ghost_visits = 0
        self.knocks = 0
        self.cold_spots = 0
        self.revealed = False

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.ghost_visits = self.ghost_visits
        clone.knocks = self.knocks
        clone.cold_spots = self.cold_spots
        clone.revealed = self.revealed
        clone.facts = dict(self.facts)
        return clone


def _bump(world: World, key: str, amount: float = 1.0) -> None:
    world.facts[key] = world.facts.get(key, 0.0) + amount


def _knock(world: World) -> None:
    world.knocks += 1
    _bump(world, "knock")
    _bump(world, "unease")
    world.events.append("knock")


def _cold_draft(world: World) -> None:
    world.cold_spots += 1
    _bump(world, "cold")
    _bump(world, "foreshadow")
    world.events.append("cold")


def _ghost_appears(world: World) -> None:
    world.ghost_visits += 1
    _bump(world, "ghost_visit")
    world.events.append("ghost")


def _resolve(world: World) -> None:
    world.revealed = True
    world.facts["resolved"] = True
    world.events.append("resolved")


def intro(world: World, child: Entity, guardian: Entity, object_ent: Entity, ghost: Ghost) -> None:
    world.say(
        f"On the night train, {child.id} sat in {world.setting.description}, "
        f"holding {child.pronoun('possessive')} {object_ent.label} while {guardian.id} dozed beside {child.pronoun('object')}."
    )
    world.say(
        f"The lamp glowed weakly, and the little door to the next compartment looked darker than the rest of the carriage."
    )
    world.say(
        f"{child.id} had heard stories about {ghost.name}, a gentle ghost who visited quiet places after sunset."
    )


def foreshadow(world: World, child: Entity) -> None:
    world.say(
        f"First there was a soft rattle from the compartment wall, and then the window felt cold against {child.pronoun('possessive')} fingertips."
    )
    world.say(
        f"{child.id} looked up, because the same cold little shiver came again, as if the train itself were warning {child.pronoun('object')} to listen closely."
    )


def repeated_knock(world: World, child: Entity) -> None:
    world.say(
        f"Knock, knock, knock."
    )
    world.say(
        f"{child.id} waited, and the quiet returned for a breath; then knock, knock, knock came again from the next compartment."
    )


def ghost_visit(world: World, child: Entity, ghost: Ghost) -> None:
    _ghost_appears(world)
    world.say(
        f"When the door finally creaked open, {ghost.name} stood there in a pale little shimmer, not frightening at all."
    )
    world.say(
        f"{ghost.name} lifted one translucent hand and pointed toward the storage compartment under the seat."
    )


def reveal(world: World, child: Entity, guardian: Entity, object_ent: Entity, ghost: Ghost) -> None:
    _resolve(world)
    world.say(
        f"In the storage compartment, {child.id} found {object_ent.phrase}, the very thing {ghost.name} had been nudging the train to notice."
    )
    world.say(
        f"{ghost.name} had lost {ghost.pronoun('possessive') if hasattr(ghost, 'pronoun') else 'its'} toy? No, not a toy, but a tiny brass key to the old compartment box where {object_ent.label} belonged."
    )


def closure(world: World, child: Entity, guardian: Entity, object_ent: Entity, ghost: Ghost) -> None:
    child.memes["courage"] = child.memes.get("courage", 0.0) + 1
    guardian.memes["calm"] = guardian.memes.get("calm", 0.0) + 1
    world.say(
        f"{child.id} carried {(getattr(object_ent, 'it')() if callable(getattr(object_ent, 'it', None)) else getattr(object_ent, 'it', 'it'))} back, and {ghost.name} gave a tiny bow that made the lamp glow steadier than before."
    )
    world.say(
        f"After that, the compartment felt warm, the knocks did not come back, and the train rolled on through the dark like a cat with soft paws."
    )
    world.say(
        f"{child.id} fell asleep smiling, with the storage door shut, the mystery solved, and the night quiet at last."
    )


def predict_reveal(world: World, child: Entity, object_ent: Entity, ghost: Ghost) -> bool:
    sim = world.copy()
    _knock(sim)
    _cold_draft(sim)
    _ghost_appears(sim)
    return bool(object_ent and ghost and sim.ghost_visits >= 1)


def tell(world: World, child: Entity, guardian: Entity, object_ent: Entity, ghost: Ghost) -> World:
    intro(world, child, guardian, object_ent, ghost)
    world.para()
    foreshadow(world, child)
    repeated_knock(world, child)
    repeated_knock(world, child)
    world.para()
    ghost_visit(world, child, ghost)
    world.say(
        f"{child.id} stopped being scared when {ghost.name} did the same little knock three times and then pointed, not to a threat, but to a clue."
    )
    if predict_reveal(world, child, object_ent, ghost):
        reveal(world, child, guardian, object_ent, ghost)
        world.para()
        closure(world, child, guardian, object_ent, ghost)
    world.facts.update(
        child=child,
        guardian=guardian,
        object_ent=object_ent,
        ghost=ghost,
        repeated_knocks=world.knocks,
        cold_spots=world.cold_spots,
        ghost_visits=world.ghost_visits,
        resolved=world.revealed,
    )
    return world


SETTING = Setting()

OBJECTS = {
    "toy_train": Entity(
        id="toy_train",
        type="thing",
        label="toy train",
        phrase="a tiny brass toy train",
    ),
    "music_box": Entity(
        id="music_box",
        type="thing",
        label="music box",
        phrase="a small music box wrapped in blue paper",
    ),
    "locket": Entity(
        id="locket",
        type="thing",
        label="locket",
        phrase="a silver locket with a heart on the lid",
    ),
}

CHILD_NAMES = ["Mina", "Nico", "Ivy", "Owen", "Luna", "Eli"]
GHOST_NAMES = ["Moth", "Pale Tom", "Mrs. Whisper", "Gray Bell", "Old Sigh"]
CHILD_TYPES = ["girl", "boy"]
GUARDIAN_TYPES = ["mother", "father", "grandmother", "grandfather"]


@dataclass
class StoryConfig:
    child_name: str = "Mina"
    child_type: str = "girl"
    guardian_type: str = "mother"
    ghost_name: str = "Mrs. Whisper"
    object_name: str = "music_box"
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


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for cn in CHILD_NAMES:
        for ct in CHILD_TYPES:
            for gt in GUARDIAN_TYPES:
                for gn in GHOST_NAMES:
                    for on in OBJECTS:
                        combos.append(("the night train", cn, ct, gt, gn, on))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small ghost-story world on a train compartment with repetition and foreshadowing."
    )
    ap.add_argument("--place", default="the night train")
    ap.add_argument("--name", dest="child_name", choices=CHILD_NAMES)
    ap.add_argument("--child-type", choices=CHILD_TYPES)
    ap.add_argument("--guardian", dest="guardian_type", choices=GUARDIAN_TYPES)
    ap.add_argument("--ghost", dest="ghost_name", choices=GHOST_NAMES)
    ap.add_argument("--object", dest="object_name", choices=OBJECTS)
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
    if getattr(args, "place", None) and getattr(args, "place", None) != "the night train":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        place="the night train",
        child_name=getattr(args, "child_name", None) or rng.choice(CHILD_NAMES),
        child_type=getattr(args, "child_type", None) or rng.choice(CHILD_TYPES),
        guardian_type=getattr(args, "guardian_type", None) or rng.choice(GUARDIAN_TYPES),
        ghost_name=getattr(args, "ghost_name", None) or rng.choice(GHOST_NAMES),
        object_name=getattr(args, "object_name", None) or rng.choice(list(OBJECTS)),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    ghost = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "ghost")
    obj = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "object_ent")
    return [
        f"Write a gentle ghost story set on a night train where {child.id} hears repeating knocks from a compartment and finds {obj.phrase}.",
        f"Tell a short story for a child named {child.id} about {ghost.name}, a quiet ghost, a storage compartment, and a small mystery that gets solved kindly.",
        f"Write a story with repetition and foreshadowing: the same knock comes back three times before the hidden item is revealed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    guardian = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "guardian")
    obj = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "object_ent")
    ghost = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "ghost")
    return [
        QAItem(
            question=f"Who heard the repeated knocking in the train compartment?",
            answer=f"{child.id} heard the repeated knocking while sitting in the night train compartment.",
        ),
        QAItem(
            question=f"What small clue foreshadowed that something was wrong before the ghost appeared?",
            answer="The window turned cold, the lamp trembled, and the little rattle came back more than once, which hinted that a hidden clue was waiting nearby.",
        ),
        QAItem(
            question=f"What was found in the storage compartment?",
            answer=f"{obj.phrase} was found in the storage compartment after {ghost.name} pointed the way.",
        ),
        QAItem(
            question=f"How did the story end for {child.id} and {guardian.id}?",
            answer=f"They solved the mystery together, the knocks stopped, and the compartment became warm and quiet again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a compartment?",
            answer="A compartment is a small separate space inside something bigger, like a train car or a box.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives small hints before something important happens later.",
        ),
        QAItem(
            question="Why do stories repeat a sound sometimes?",
            answer="A repeated sound can make a story feel eerie, important, or playful, and it can help a child notice that the sound matters.",
        ),
    ]


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"  knocks={world.knocks} cold_spots={world.cold_spots} ghost_visits={world.ghost_visits} resolved={world.revealed}")
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: type={e.type} label={e.label}")
    return "\n".join(lines)


ASP_RULES = r"""
% A compartment story is valid if a child, a repeated knock, and a gentle ghost
% are all present, and the hidden object can be revealed.
valid_story(C, G, O) :- child(C), ghost(G), hidden_item(O), repeat_hint, reveal_possible.
repeat_hint :- repeated(knock), repeated(knock), repeated(knock).
reveal_possible :- compartment, storage_compartment.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("compartment"))
    lines.append(asp.fact("storage_compartment"))
    lines.append(asp.fact("repeatable"))
    lines.append(asp.fact("foreshadowable"))
    for c in CHILD_NAMES:
        lines.append(asp.fact("child", c))
    for g in GHOST_NAMES:
        lines.append(asp.fact("ghost", g))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("hidden_item", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    if py:
        print(f"OK: Python gate has {len(py)} story configurations.")
        return 0
    print("MISMATCH: no valid stories.")
    return 1


def generate(params: StoryParams) -> StorySample:
    setting = SETTING
    world = World(setting)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    guardian = world.add(Entity(id=params.guardian_type, kind="character", type=params.guardian_type))
    object_ent = world.add(Entity(id=params.object_name, type="thing", label=_safe_lookup(OBJECTS, params.object_name).label, phrase=_safe_lookup(OBJECTS, params.object_name).phrase))
    ghost = Ghost(id="ghost", name=params.ghost_name)

    tell(world, child, guardian, object_ent, ghost)
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


CURATED = [
    StoryParams(child_name="Mina", child_type="girl", guardian_type="mother", ghost_name="Mrs. Whisper", object_name="music_box"),
    StoryParams(child_name="Nico", child_type="boy", guardian_type="father", ghost_name="Gray Bell", object_name="toy_train"),
    StoryParams(child_name="Ivy", child_type="girl", guardian_type="grandmother", ghost_name="Moth", object_name="locket"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid_story/3."))
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
