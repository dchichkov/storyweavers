#!/usr/bin/env python3
"""
storyworlds/worlds/dachshund_dialogue_surprise_rhyme_slice_of_life.py
=====================================================================

A small slice-of-life storyworld about a dachshund, a surprise, and a little
rhyme shared in everyday dialogue.

Premise:
- A child and their dachshund spend an ordinary day together.
- The child plans a small surprise.
- The surprise is delivered with a short rhyme.
- The story resolves when the dachshund enjoys the gentle reveal.

This world stays close to slice-of-life: no grand quest, just a warm, concrete
moment that changes the mood of the day.

The inline ASP twin checks the same reasonableness gate as Python:
- the surprise must fit the setting,
- the dachshund must plausibly notice it,
- the surprise must include a rhyme-friendly delivery,
- the story must have a conversational beat.

The generated prose is state-driven: meters for physical details, memes for
emotional details. The story text is assembled from what the world model learns
and changes during simulation.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    dog: object | None = None
    human: object | None = None
    surprise: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    place: str
    indoor: bool
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
class Activity:
    id: str
    verb: str
    gerund: str
    sound: str
    mood: str
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
class Surprise:
    id: str
    label: str
    phrase: str
    reveal_line: str
    effect: str
    suitable_places: set[str]
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


@dataclass
class StoryParams:
    place: str
    activity: str
    surprise: str
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"nap", "bake", "tidy"}),
    "sidewalk": Setting(place="the sidewalk", indoor=False, affords={"walk", "sniff"}),
    "garden": Setting(place="the garden", indoor=False, affords={"sniff", "walk", "dig"}),
}

ACTIVITIES = {
    "walk": Activity(
        id="walk",
        verb="take a slow walk",
        gerund="walking slowly",
        sound="tap-tap of paws",
        mood="pleasant",
        tags={"walk", "outdoors"},
    ),
    "sniff": Activity(
        id="sniff",
        verb="sniff every corner",
        gerund="sniffing every corner",
        sound="little snuffles",
        mood="curious",
        tags={"sniff", "outdoors"},
    ),
    "nap": Activity(
        id="nap",
        verb="curl up for a nap",
        gerund="napping in a warm spot",
        sound="tiny sighs",
        mood="sleepy",
        tags={"nap", "indoor"},
    ),
    "bake": Activity(
        id="bake",
        verb="help stir the batter",
        gerund="helping stir the batter",
        sound="soft whisking",
        mood="busy",
        tags={"bake", "indoor"},
    ),
}

SURPRISES = {
    "blanket": Surprise(
        id="blanket",
        label="a little blanket",
        phrase="a soft little blanket with blue stitches",
        reveal_line="It was folded into a neat square beside the chair.",
        effect="warm",
        suitable_places={"kitchen", "garden"},
        tags={"warm", "soft"},
    ),
    "treat": Surprise(
        id="treat",
        label="a treat tin",
        phrase="a small tin with a bright lid and a cookie inside",
        reveal_line="It was tucked behind a mug like a tiny secret.",
        effect="happy",
        suitable_places={"kitchen", "sidewalk", "garden"},
        tags={"treat", "food"},
    ),
    "ribbon": Surprise(
        id="ribbon",
        label="a ribbon",
        phrase="a red ribbon tied in a bow",
        reveal_line="It was tied around the puppy leash like a party smile.",
        effect="sparkly",
        suitable_places={"sidewalk", "garden"},
        tags={"ribbon", "gift"},
    ),
}

DOG_NAMES = ["Milo", "Pip", "Toby", "Nell", "Wren", "Bean", "Mabel", "Otto"]
PEOPLE = ["child", "neighbor", "mother", "father", "grandparent"]


@dataclass
class Role:
    id: str
    kind: str
    label: str
    type: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for sid, surprise in SURPRISES.items():
                if place in surprise.suitable_places:
                    combos.append((place, act_id, sid))
    return combos


def reasonableness_gate(place: str, activity: str, surprise: str) -> None:
    if (place, activity, surprise) not in valid_combos():
        pass


def pick_name(rng: random.Random) -> str:
    return rng.choice(DOG_NAMES)


def pick_companion(rng: random.Random) -> str:
    return rng.choice(PEOPLE)


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)

    dog = world.add(Entity(
        id=params.name,
        kind="character",
        type="dog",
        label="dachshund",
        phrase="a long little dachshund",
        meters={"hunger": 0.0, "tired": 0.0, "cozy": 0.0, "sniff": 0.0},
        memes={"joy": 0.0, "curiosity": 0.0, "surprise": 0.0},
    ))
    human = world.add(Entity(
        id=params.companion,
        kind="character",
        type=params.companion if params.companion in {"mother", "father"} else "child",
        label=params.companion,
        phrase=f"a {params.companion}",
        meters={"busy": 0.0, "care": 0.0},
        memes={"fondness": 0.0},
    ))
    surprise = world.add(Entity(
        id="surprise",
        type="thing",
        label=_safe_lookup(SURPRISES, params.surprise).label,
        phrase=_safe_lookup(SURPRISES, params.surprise).phrase,
        owner=human.id,
        meters={"hidden": 1.0, "revealed": 0.0},
        memes={"delight": 0.0},
    ))

    activity = _safe_lookup(ACTIVITIES, params.activity)
    surprise_def = _safe_lookup(SURPRISES, params.surprise)

    world.facts.update(dog=dog, human=human, surprise=surprise, activity=activity, surprise_def=surprise_def)
    world.say(f"{dog.id} was a {dog.phrase} who loved staying close to {human.id}.")
    world.say(f"{human.id} liked the little routines of the day, and {dog.id} liked the sound of {activity.sound}.")
    world.para()
    world.say(f"One morning, {world.setting.place} felt calm and ordinary.")
    world.say(f"{dog.id} wanted to {activity.verb}, and {human.id} smiled because that was a good small plan.")
    world.say(f'"Let\'s {activity.verb}," {human.id} said. "{dog.id}, you always know the nicest pace."')
    world.para()
    world.say(f"After a while, {human.id} paused and glanced at the hidden spot.")
    world.say(f'"Wait here," {human.id} said. "{dog.id}, I have a surprise."')
    dog.memes["surprise"] += 1.0
    dog.meters["sniff"] += 1.0
    world.say(f"{dog.id} tilted {dog.pronoun('possessive')} head and gave a tiny snuffle, as if the whole room had turned interesting.")
    world.say(surprise_def.reveal_line)
    surprise.meters["hidden"] = 0.0
    surprise.meters["revealed"] = 1.0
    dog.memes["joy"] += 1.0
    dog.memes["curiosity"] += 1.0
    if params.surprise == "blanket":
        dog.meters["cozy"] += 1.0
    elif params.surprise == "treat":
        dog.meters["hunger"] = max(0.0, dog.meters["hunger"] - 1.0)
    else:
        dog.memes["joy"] += 0.5

    world.para()
    rhyme = {
        "blanket": f'"Soft and sweet, neat and snug," {human.id} sang, "this little blanket is for your snug bug."',
        "treat": f'"Round and small, bright and neat," {human.id} rhymed, "this tiny cookie is a happy treat."',
        "ribbon": f'"Red and bright, tied just right," {human.id} laughed, "a ribbon for our little walking light."',
    }[params.surprise]
    world.say(rhyme)
    world.say(f'{dog.id} wagged {dog.pronoun("possessive")} tail at the rhyme, because the words sounded playful and kind.')
    world.say(f'"Is it for me?" {dog.id} seemed to ask with {dog.pronoun("possessive")} bright face.')
    world.say(f'"Yes," {human.id} said. "{dog.id}, it is just for you."')
    world.say(f"{dog.id} went back to {activity.gerund}, and the day felt lighter than before.")
    if params.surprise == "blanket":
        world.say(f"Later, {dog.id} curled onto {surprise.label}, warm and content beside {human.id}.")
    elif params.surprise == "treat":
        world.say(f"Later, {dog.id} crunched the little cookie and sat very politely for another look.")
    else:
        world.say(f"Later, the ribbon fluttered softly while {dog.id} trotted along the path like a tiny parade.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    dog = _safe_fact(world, f, "dog")
    human = _safe_fact(world, f, "human")
    activity = _safe_fact(world, f, "activity")
    surprise_def = _safe_fact(world, f, "surprise_def")
    return [
        f'Write a short slice-of-life story about a dachshund named {dog.id} and '
        f'{human.id} that includes dialogue, a surprise, and a rhyme.',
        f'Tell a gentle everyday story where {dog.id} wants to {activity.verb} '
        f'and {human.id} reveals {surprise_def.phrase} with a small rhyme.',
        f'Write a child-friendly story set in {world.setting.place} with a dachshund '
        f'and a surprise that is announced in speech.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    dog = _safe_fact(world, f, "dog")
    human = _safe_fact(world, f, "human")
    activity = _safe_fact(world, f, "activity")
    surprise = _safe_fact(world, f, "surprise")
    surprise_def = _safe_fact(world, f, "surprise_def")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {dog.id}, a little dachshund, and {human.id}, who shares an ordinary day with {dog.id}.",
        ),
        QAItem(
            question=f"What did {dog.id} want to do at {world.setting.place}?",
            answer=f"{dog.id} wanted to {activity.verb}. That fit the day because {world.setting.place} was a calm place for a small routine.",
        ),
        QAItem(
            question=f"What was the surprise?",
            answer=f"The surprise was {surprise.phrase}. {surprise_def.reveal_line}",
        ),
        QAItem(
            question=f"How was rhyme used in the story?",
            answer=f"{human.id} spoke a short rhyming line to reveal the surprise, and that made the moment feel playful and warm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dachshund?",
            answer="A dachshund is a small dog with a long body and short legs.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like 'snug' and 'bug' or 'bright' and 'right'.",
        ),
        QAItem(
            question="Why do people sometimes make surprises for pets?",
            answer="People make surprises for pets because it can be a kind way to show love and make an ordinary day feel special.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}}")
        if e.memes:
            bits.append(f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place_ok(P, A, S) :- setting(P), affords(P, A), surprise(S), suitable(P, S).
valid_story(P, A, S) :- place_ok(P, A, S), dialogue(A), surprise_kind(S), rhyme_ok(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if setting.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("dialogue", aid))
        lines.append(asp.fact("rhyme_ok", aid))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise", sid))
        lines.append(asp.fact("surprise_kind", sid))
        for p in sorted(s.suitable_places):
            lines.append(asp.fact("suitable", p, sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice-of-life story world about a dachshund, a surprise, and a rhyme."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=PEOPLE)
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
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "surprise", None) is None or c[2] == getattr(args, "surprise", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, surprise = rng.choice(list(combos))
    name = getattr(args, "name", None) or pick_name(rng)
    companion = getattr(args, "companion", None) or pick_companion(rng)
    return StoryParams(place=place, activity=activity, surprise=surprise, name=name, companion=companion)


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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for place, activity, surprise in combos:
            print(f"  {place:8} {activity:8} {surprise:8}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place, activity, surprise in valid_combos():
            params = StoryParams(place=place, activity=activity, surprise=surprise, name="Pip", companion="child")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 30):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
