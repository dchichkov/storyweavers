#!/usr/bin/env python3
"""
storyworlds/worlds/snug_repetition_mystery.py
=============================================

A tiny mystery storyworld with a snug feeling and a repeated-clue structure.

Premise:
- A child notices a cozy, snug thing is missing.
- The search keeps circling the same spots, repeating clues.
- A careful pattern in the repeated search reveals where the thing was tucked.

The domain is deliberately small:
- one hero
- one helper
- one cherished snug item
- one hiding place
- one revealing clue pattern

The simulated world carries both physical state (meters) and emotional state
(memes), and the story is rendered from the way those states change.
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
# Small domain registries
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

@dataclass(frozen=True)
class Setting:
    name: str
    detail: str
    hiding_spots: tuple[str, ...]
    clue: str
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


@dataclass(frozen=True)
class Thing:
    name: str
    phrase: str
    snugness: str
    usual_place: str
    hidden_in: str
    is_plush: bool = False
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


@dataclass(frozen=True)
class Helper:
    name: str
    label: str
    method: str
    reassurance: str
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


SETTINGS = {
    "hallway": Setting(
        name="the hallway",
        detail="The hallway was narrow and quiet, with shoes lined up like little soldiers.",
        hiding_spots=("shoe rack", "umbrella stand", "coat hook"),
        clue="a soft scuff near the door",
    ),
    "bedroom": Setting(
        name="the bedroom",
        detail="The bedroom was warm and dim, with a lamp making a soft yellow circle.",
        hiding_spots=("pillow pile", "toy chest", "blanket fold"),
        clue="a tiny bump under the blanket",
    ),
    "kitchen": Setting(
        name="the kitchen",
        detail="The kitchen smelled like toast, and the table stood in the middle like a calm island.",
        hiding_spots=("bread box", "tea tin", "chair seat"),
        clue="a crumb trail by the table leg",
    ),
    "porch": Setting(
        name="the porch",
        detail="The porch boards were cool, and the rain drum on the roof made a steady tap-tap.",
        hiding_spots=("doormat corner", "rain boot", "watering can"),
        clue="a wet line by the mat",
    ),
}

THINGS = {
    "scarf": Thing(
        name="scarf",
        phrase="a snug striped scarf",
        snugness="snug and soft",
        usual_place="the coat hook",
        hidden_in="the coat pocket",
    ),
    "hat": Thing(
        name="hat",
        phrase="a snug red hat",
        snugness="warm and snug",
        usual_place="the basket by the door",
        hidden_in="the basket lining",
    ),
    "bunny": Thing(
        name="bunny",
        phrase="a snug plush bunny",
        snugness="soft and snug",
        usual_place="the pillow pile",
        hidden_in="the blanket fold",
        is_plush=True,
    ),
}

HELPERS = {
    "mom": Helper(
        name="mom",
        label="Mom",
        method="look again, then look one more time",
        reassurance="Some clues only make sense when you notice them twice.",
    ),
    "dad": Helper(
        name="dad",
        label="Dad",
        method="count the clues one by one",
        reassurance="If a clue repeats, it wants you to pay attention.",
    ),
    "grandma": Helper(
        name="grandma",
        label="Grandma",
        method="check the same spot in a careful order",
        reassurance="Mysteries often hide in plain sight.",
    ),
}

NAMES = ["Milo", "Mina", "Pip", "Lena", "Toby", "Nora", "June", "Owen"]
TRAITS = ["curious", "careful", "quiet", "bright", "small", "brave"]


# ---------------------------------------------------------------------------
# Shared result world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    found: bool = False
    hidden_place: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    thing: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "mom", "grandmother", "grandma"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "dad", "grandfather", "grandpa"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    world: object | None = None
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


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
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
class StoryParams:
    setting: str
    thing: str
    helper: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
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
    setting = _safe_lookup(SETTINGS, params.setting)
    thing_cfg = _safe_lookup(THINGS, params.thing)
    helper_cfg = _safe_lookup(HELPERS, params.helper)
    world = World(setting=setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="child",
        label=params.name,
        meters={"worry": 0.0, "hope": 0.0, "calm": 0.0},
        memes={"worry": 0.0, "hope": 0.0, "calm": 0.0},
    ))
    helper = world.add(Entity(
        id=helper_cfg.name,
        kind="character",
        type=params.helper,
        label=helper_cfg.label,
        meters={"calm": 1.0},
        memes={"calm": 1.0},
    ))
    thing = world.add(Entity(
        id=thing_cfg.name,
        kind="thing",
        type=thing_cfg.name,
        label=thing_cfg.name,
        phrase=thing_cfg.phrase,
        owner=hero.id,
        hidden_place=thing_cfg.hidden_in,
        found=False,
    ))

    # Act 1: the cozy object is noticed as missing.
    world.say(
        f"{hero.id} was a {params.trait} child who loved {thing_cfg.phrase}."
    )
    world.say(
        f"Every morning, {thing_cfg.name} lived in {thing_cfg.usual_place}, because it felt "
        f"{thing_cfg.snugness} there."
    )
    world.para()
    world.say(setting.detail)
    world.say(
        f"But one day, {hero.id} looked at {thing_cfg.usual_place} and saw only empty space."
    )
    hero.meters["worry"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id}'s worry rose, because the missing {thing_cfg.name} made the room feel less snug."
    )

    # Act 2: repeated searching.
    world.para()
    search_spots = list(setting.hiding_spots)
    repeats = [search_spots[0], search_spots[1], search_spots[0]]
    clues = []
    for spot in repeats:
        if spot == thing_cfg.hidden_in:
            clue = f"there was a soft shape tucked in {spot}"
        elif spot == "coat hook" and thing_cfg.name == "scarf":
            clue = "the hook looked too bare, as if something had slipped away"
        elif spot == "blanket fold" and thing_cfg.name == "bunny":
            clue = "the blanket fold held a little bump that kept showing up"
        else:
            clue = f"nothing there, only {setting.clue}"
        clues.append(clue)
        hero.meters["worry"] += 0.2
        hero.memes["worry"] += 0.2
        world.say(
            f"{hero.id} looked in the {spot}, and then looked again in the {spot}, but {clue}."
        )

    world.para()
    helper.say = helper_cfg.label  # type: ignore[attr-defined]
    world.say(
        f"{helper_cfg.label} came over and said, \"{helper_cfg.reassurance}\""
    )
    world.say(
        f"Together they tried {helper_cfg.method.lower()}, because the same clue kept repeating."
    )
    hero.meters["hope"] += 1
    hero.memes["hope"] += 1

    # Act 3: the repeated clue reveals the hiding place.
    world.para()
    world.say(
        f"They checked the {thing_cfg.hidden_in}, where the clue finally made sense."
    )
    thing.found = True
    hero.meters["worry"] = 0.0
    hero.memes["worry"] = 0.0
    hero.meters["calm"] += 1
    hero.memes["calm"] += 1
    world.say(
        f"There was {thing_cfg.phrase}, tucked {thing_cfg.snugness} into the {thing_cfg.hidden_in}."
    )
    world.say(
        f"{hero.id} smiled, hugged {thing_cfg.name} close, and the room felt snug again."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        thing=thing,
        setting=setting,
        thing_cfg=thing_cfg,
        helper_cfg=helper_cfg,
        clues=clues,
        repeated_spot=repeats[0],
        hidden_spot=thing_cfg.hidden_in,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a young child about a snug {f["thing_cfg"].name} that goes missing and is found by noticing a repeated clue.',
        f"Tell a cozy detective story where {f['hero'].id} keeps checking the same places and the repeating clue leads to {f['thing_cfg'].hidden_in}.",
        f'Write a gentle repetition mystery using the word "snug" and ending with the missing {f["thing_cfg"].name} found at last.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    thing_cfg = _safe_fact(world, f, "thing_cfg")
    helper_cfg = _safe_fact(world, f, "helper_cfg")
    setting = _safe_fact(world, f, "setting")

    return [
        QAItem(
            question=f"What went missing in {hero.id}'s story?",
            answer=f"The missing thing was {thing_cfg.phrase}. It usually stayed in {thing_cfg.usual_place}, but then it vanished.",
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the mystery?",
            answer=f"{helper_cfg.label} helped {hero.id}. {helper_cfg.label} reminded {hero.id} to notice the repeating clue instead of rushing.",
        ),
        QAItem(
            question=f"Where was the thing finally found?",
            answer=f"It was found in {thing_cfg.hidden_in}, after they checked the same places more than once.",
        ),
        QAItem(
            question=f"Why did the repeated clue matter?",
            answer=f"The repeated clue mattered because it kept pointing back to the same hiding place in {setting.name}, which helped {hero.id} solve the mystery.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does snug mean?",
            answer="Snug means cozy, warm, and comfortably close, like something that fits just right.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps someone figure out an answer in a mystery.",
        ),
        QAItem(
            question="Why can repeating a clue help solve a mystery?",
            answer="When a clue repeats, it can show a pattern, and patterns often help people notice where to look next.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(S) :- setting_fact(S).
thing(T) :- thing_fact(T).
helper(H) :- helper_fact(H).

repeated(Spot) :- clue(Spot), clue(Spot).
resolved(Thing) :- hidden_in(Thing, Spot), repeated(Spot).

#show repeated/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_fact", s))
    for t in THINGS:
        lines.append(asp.fact("thing_fact", t))
    for h in HELPERS:
        lines.append(asp.fact("helper_fact", h))
    for s in SETTINGS.values():
        for spot in s.hiding_spots:
            lines.append(asp.fact("clue", spot))
    for t in THINGS.values():
        lines.append(asp.fact("hidden_in", t.name, t.hidden_in))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show resolved/1."))
    resolved = set(asp.atoms(model, "resolved"))
    expected = {(t.name,) for t in THINGS.values()}
    if resolved == expected:
        print(f"OK: ASP resolved-set matches the Python registry ({len(resolved)} things).")
        return 0
    print("MISMATCH between ASP and Python registry:")
    print("  ASP:", sorted(resolved))
    print("  PY :", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Parameter resolution and generation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_name, setting in SETTINGS.items():
        for thing_name, thing in THINGS.items():
            for helper_name in HELPERS:
                if thing.hidden_in in setting.hiding_spots:
                    combos.append((setting_name, thing_name, helper_name))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A snug repetition mystery storyworld.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--thing", choices=sorted(THINGS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--name", choices=NAMES)
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
    combos = valid_combos()
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "thing", None):
        combos = [c for c in combos if c[1] == getattr(args, "thing", None)]
    if getattr(args, "helper", None):
        combos = [c for c in combos if c[2] == getattr(args, "helper", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    setting, thing, helper = rng.choice(list(combos))
    return StoryParams(
        setting=setting,
        thing=thing,
        helper=helper,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        if e.hidden_place:
            bits.append(f"hidden_place={e.hidden_place!r}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: " + ", ".join(bits))
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
        print(asp_program("#show resolved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show resolved/1."))
        atoms = sorted(set(asp.atoms(model, "resolved")))
        print(f"{len(atoms)} resolved things:")
        for atom in atoms:
            print(f"  {atom[0]}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(setting="bedroom", thing="bunny", helper="grandma", name="Mina", trait="curious"),
            StoryParams(setting="hallway", thing="scarf", helper="mom", name="Pip", trait="careful"),
            StoryParams(setting="kitchen", thing="hat", helper="dad", name="Toby", trait="bright"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 25):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
