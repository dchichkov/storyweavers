#!/usr/bin/env python3
"""
A tiny mythic storyworld about Lly learning bravery.

This world simulates a child hero facing a small but frightening trial in a
myth-like setting. The hero starts cautious, receives a warning from an elder,
stands before a dark place or noisy creature, and chooses brave action. The
story turns on a concrete act of courage, and the ending shows how the world
changed: fear softens, the helper is safe, and the hero is remembered as brave.

The domain is intentionally small and constraint-checked:
- one hero named Lly
- one mythic trial
- one useful tool or blessing
- one shift from fear to bravery

The prose should read like a short child-facing myth.
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


BRAVERY_THRESHOLD = 1.0



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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    elder: object | None = None
    hero: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "hero", "child"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    id: str
    label: str
    mood: str
    danger: str
    history: str
    supports: set[str] = field(default_factory=set)
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


@dataclass
class Trial:
    id: str
    verb: str
    fear: str
    risk: str
    sign: str
    outcome: str
    keyword: str
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
class Gift:
    id: str
    label: str
    phrase: str
    use: str
    protects: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trial_sign: str = ""

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

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

        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.trial_sign = self.trial_sign
        return clone


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    lly = world.get("lly")
    if lly.memes.get("bravery", 0.0) < BRAVERY_THRESHOLD:
        return out
    if world.trial_sign and ("brave_turn", world.trial_sign) not in world.fired:
        world.fired.add(("brave_turn", world.trial_sign))
        out.append("__brave_turn__")
    return out


def _r_safe(world: World) -> list[str]:
    out: list[str] = []
    lly = world.get("lly")
    if lly.memes.get("bravery", 0.0) < BRAVERY_THRESHOLD:
        return out
    for entity in list(world.entities.values()):
        if entity.id == "lly":
            continue
        if entity.meters.get("hurt", 0.0) >= BRAVERY_THRESHOLD:
            sig = ("safe", entity.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            entity.meters["hurt"] = 0.0
            out.append(f"{entity.label or entity.id} was safe at last.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    for rule in (_r_bravery, _r_safe):
        sents = rule(world)
        for s in sents:
            if s != "__brave_turn__":
                produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def mythic_opening(place: Place) -> str:
    return f"Long ago, when {place.label} was still full of old songs and watchful winds, "


def intro(world: World, hero: Entity) -> None:
    world.say(
        f"{mythic_opening(world.place)}there lived a small hero named {hero.id}. "
        f"{hero.id} listened closely to thunder, birds, and every tale told by the fire."
    )


def love_of_place(world: World, hero: Entity) -> None:
    hero.memes["belonging"] = hero.memes.get("belonging", 0.0) + 1
    world.say(
        f"{hero.id} loved {world.place.label}, where the stones were old and the air "
        f"felt full of wonder."
    )


def gift(world: World, hero: Entity, gift_obj: Entity) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    gift_obj.owner = hero.id
    world.say(
        f"Before the trial, {hero.id}'s elder gave {hero.pronoun('object')} {gift_obj.phrase}."
    )


def warning(world: World, elder: Entity, hero: Entity, trial: Trial) -> None:
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    world.say(
        f'"Beware the {trial.fear}," said {elder.label}. '
        f'"Many have heard it and turned away."'
    )
    world.say(
        f"But {hero.id} looked toward the {trial.keyword} and felt {trial.risk} in {hero.pronoun('possessive')} chest."
    )


def hesitate(world: World, hero: Entity, trial: Trial) -> None:
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    world.say(
        f"{hero.id} took one small step, then stopped. "
        f"The {trial.sign} seemed louder than before."
    )


def choose_bravery(world: World, hero: Entity, trial: Trial, gift_obj: Entity) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
    hero.meters["action"] = hero.meters.get("action", 0.0) + 1
    world.trial_sign = trial.sign
    world.say(
        f"Then {hero.id} held {hero.pronoun('possessive')} {gift_obj.label} close and chose to {trial.verb}."
    )
    propagate(world, narrate=True)


def resolve(world: World, hero: Entity, trial: Trial, gift_obj: Entity, elder: Entity) -> None:
    hero.memes["fear"] = 0.0
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    world.say(
        f"The {trial.sign} changed at once. What had seemed sharp and wild became {trial.outcome}."
    )
    world.say(
        f"{hero.id} stood still in the quiet after, and {elder.label} smiled. "
        f'"That is how a brave heart learns its name," said {elder.label}.'
    )
    world.say(
        f"From that day on, the people of {world.place.label} told of {hero.id} "
        f"and the {trial.keyword}, and they said {hero.id} had become brave."
    )


def tell_story(place: Place, trial: Trial, gift_obj: Gift) -> World:
    world = World(place)
    hero = world.add(Entity(id="lly", kind="character", type="child", label="Lly"))
    elder = world.add(Entity(id="elder", kind="character", type="elder", label="the elder"))
    tool = world.add(Entity(id="gift", kind="thing", type="thing", label=gift_obj.label, phrase=gift_obj.phrase))

    world.facts.update(hero=hero, elder=elder, trial=trial, gift=tool, place=place)

    intro(world, hero)
    world.para()
    love_of_place(world, hero)
    gift(world, hero, tool)
    warning(world, elder, hero, trial)
    hesitate(world, hero, trial)
    world.para()
    choose_bravery(world, hero, trial, tool)
    resolve(world, hero, trial, tool, elder)
    return world


PLACES = {
    "hill": Place(
        id="hill",
        label="the high hill",
        mood="windy",
        danger="a steep drop",
        history="where old stones keep the sunset",
        supports={"stand", "watch", "hear"},
    ),
    "grove": Place(
        id="grove",
        label="the shadow grove",
        mood="still",
        danger="a dark echo",
        history="where roots knot around sleeping water",
        supports={"stand", "listen", "wait"},
    ),
    "shore": Place(
        id="shore",
        label="the silver shore",
        mood="bright",
        danger="a roaring wave",
        history="where shells shine like tiny moons",
        supports={"stand", "cross", "sing"},
    ),
}

TRIALS = {
    "echo": Trial(
        id="echo",
        verb="call back to the echo",
        fear="echo",
        risk="his knees trembled",
        sign="echo",
        outcome="a friendly answer from the trees",
        keyword="echo",
        tags={"sound", "forest"},
    ),
    "wave": Trial(
        id="wave",
        verb="step toward the wave",
        fear="wave",
        risk="his breath caught",
        sign="wave",
        outcome="foam that rolled in like a white ribbon",
        keyword="wave",
        tags={"water", "sea"},
    ),
    "drop": Trial(
        id="drop",
        verb="walk to the edge",
        fear="drop",
        risk="his heart leapt",
        sign="drop",
        outcome="a safe path of flat stone",
        keyword="drop",
        tags={"height", "stone"},
    ),
}

GIFTS = {
    "lamp": Gift(
        id="lamp",
        label="a little lamp",
        phrase="a little lamp with a gold flame",
        use="light",
        protects={"dark"},
        tags={"light", "night"},
    ),
    "cloak": Gift(
        id="cloak",
        label="a blue cloak",
        phrase="a blue cloak against the wind",
        use="warmth",
        protects={"wind"},
        tags={"wind", "cloth"},
    ),
    "cord": Gift(
        id="cord",
        label="a bright cord",
        phrase="a bright cord to mark the path",
        use="guide",
        protects={"lost"},
        tags={"path", "guide"},
    ),
}

CURATED = [
    ("grove", "echo", "lamp"),
    ("shore", "wave", "cloak"),
    ("hill", "drop", "cord"),
]


@dataclass
class StoryParams:
    place: str
    trial: str
    gift: str
    seed: Optional[int] = None
    params: object | None = None
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for trial_id in place.supports:
            if trial_id not in TRIALS:
                continue
            for gift_id, gift in GIFTS.items():
                trial = _safe_lookup(TRIALS, trial_id)
                if trial_id == "echo" and "light" in gift.tags:
                    combos.append((place_id, trial_id, gift_id))
                elif trial_id == "wave" and "wind" in gift.tags:
                    combos.append((place_id, trial_id, gift_id))
                elif trial_id == "drop" and "guide" in gift.tags:
                    combos.append((place_id, trial_id, gift_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for a child named lly about bravery at {f["place"].label}.',
        f'Tell a story where lly faces the {f["trial"].keyword} and finds courage with {f["gift"].label}.',
        f'Write a gentle legend in which lly is afraid at first, then brave by the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    trial = _safe_fact(world, f, "trial")
    place = _safe_fact(world, f, "place")
    gift = _safe_fact(world, f, "gift")
    elder = _safe_fact(world, f, "elder")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about lly, a small child who stood at {place.label} and learned bravery.",
        ),
        QAItem(
            question=f"What did the elder warn lly about?",
            answer=f"The elder warned lly about the {trial.fear}, which sounded frightening at first.",
        ),
        QAItem(
            question=f"What helped lly face the trial?",
            answer=f"Lly was given {gift.phrase}, and that gift helped lly choose to {trial.verb}.",
        ),
        QAItem(
            question=f"How did lly feel before the brave choice?",
            answer=f"Before the brave choice, lly felt fear and hesitated when the {trial.sign} seemed loud.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with lly brave, the danger turned gentle, and the elder speaking proudly of the brave heart.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = []
    if f["trial"].id == "echo":
        out.append(
            QAItem(
                question="What is an echo?",
                answer="An echo is a sound that comes back after it is spoken into a place that reflects the sound.",
            )
        )
    if f["trial"].id == "wave":
        out.append(
            QAItem(
                question="What is a wave?",
                answer="A wave is moving water, often seen in the sea or on a lake when wind pushes the surface.",
            )
        )
    if f["gift"].id == "lamp":
        out.append(
            QAItem(
                question="What does a lamp do?",
                answer="A lamp gives light, which helps people see in dark places.",
            )
        )
    if f["gift"].id == "cloak":
        out.append(
            QAItem(
                question="What does a cloak do?",
                answer="A cloak covers the body and can help block cold wind.",
            )
        )
    if f["gift"].id == "cord":
        out.append(
            QAItem(
                question="What is a cord used for?",
                answer="A cord can help mark a path or hold things together so they are easier to follow.",
            )
        )
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
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"trial_sign={world.trial_sign}")
    return "\n".join(lines)


ASP_RULES = r"""
place(hill). place(grove). place(shore).

trial(echo). trial(wave). trial(drop).

gift(lamp). gift(cloak). gift(cord).

supports(grove,echo).
supports(shore,wave).
supports(hill,drop).

helps(lamp,echo).
helps(cloak,wave).
helps(cord,drop).

valid(P,T,G) :- supports(P,T), helps(G,T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t in TRIALS:
        lines.append(asp.fact("trial", t))
    for g in GIFTS:
        lines.append(asp.fact("gift", g))
    for place_id, trial_id, gift_id in valid_combos():
        lines.append(asp.fact("supports", place_id, trial_id))
        lines.append(asp.fact("helps", gift_id, trial_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mythic storyworld about lly and bravery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trial", choices=TRIALS)
    ap.add_argument("--gift", choices=GIFTS)
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
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "trial", None):
        combos = [c for c in combos if c[1] == getattr(args, "trial", None)]
    if getattr(args, "gift", None):
        combos = [c for c in combos if c[2] == getattr(args, "gift", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, trial, gift = rng.choice(list(combos))
    return StoryParams(place=place, trial=trial, gift=gift)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(_safe_lookup(PLACES, params.place), _safe_lookup(TRIALS, params.trial), _safe_lookup(GIFTS, params.gift))
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place, trial, gift in CURATED:
            params = StoryParams(place=place, trial=trial, gift=gift, seed=base_seed)
            samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
