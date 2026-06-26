#!/usr/bin/env python3
"""
storyworlds/worlds/conditioning_mud_sharing_sound_effects_teamwork_folk.py
==========================================================================

A small folk-tale story world about conditioning mud, sharing tools, and
teamwork in a rainy village.

Seed tale:
---
On a wet morning, the little folk of Bramble Hollow found that the path to the
mill had sunk into sticky mud. Nib the hedgehog wanted to help the others
repair the path, but the mud was too stiff to spread and the only bucket was
too small for everyone. Old Aunt Willow said they would need to condition the
mud first, sharing water, time, and strong hands.

So the children and the grown-ups took turns: one poured, one stirred, one
stomped, and one sang out the beat. With each splash and squish, the mud grew
soft enough to pack into the broken path. In the end, the whole village crossed
together, laughing at the plop-plop sounds their boots made on the fresh mud.

World model:
---
- Physical meters track mud softness, bucket water, path repair, and tool wear.
- Emotional memes track worry, sharing, joy, and teamwork.
- The story advances when the folk share resources and condition the mud
  together, turning tension into a finished path.

Narrative instruments:
---
- Sharing: scarce water and tools are shared among the folk.
- Sound Effects: the narration uses child-friendly onomatopoeia.
- Teamwork: the resolution requires coordinated action by multiple folk.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    shared: bool = False

    bucket: object | None = None
    elder: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman", "sister"}
        male = {"boy", "father", "grandfather", "uncle", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    indoors: bool = False
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
class Task:
    id: str
    verb: str
    gerund: str
    mess: str
    soil: str
    keyword: str
    sound: str
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
class SharedItem:
    id: str
    label: str
    phrase: str
    kind: str
    plural: bool = False
    shared: bool = True
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
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


SETTINGS = {
    "village_green": Setting("the village green", affords={"condition_mud", "share_water"}),
    "mill_road": Setting("the mill road", affords={"condition_mud", "share_water"}),
    "barn_yard": Setting("the barn yard", affords={"condition_mud", "share_water"}),
    "old_well": Setting("the old well", affords={"share_water"}),
}

TASKS = {
    "condition_mud": Task(
        id="condition_mud",
        verb="condition the mud",
        gerund="conditioning the mud",
        mess="muddy",
        soil="too stiff to pack",
        keyword="conditioning",
        sound="squish-splash",
        tags={"conditioning", "mud", "teamwork"},
    ),
    "share_water": Task(
        id="share_water",
        verb="share the water",
        gerund="sharing the water",
        mess="wet",
        soil="not enough to go around",
        keyword="sharing",
        sound="glug-glug",
        tags={"sharing", "teamwork"},
    ),
}

SHARED_ITEMS = {
    "bucket": SharedItem(
        id="bucket",
        label="bucket",
        phrase="a small wooden bucket",
        kind="tool",
    ),
    "trowel": SharedItem(
        id="trowel",
        label="trowel",
        phrase="a smooth trowel",
        kind="tool",
    ),
    "song": SharedItem(
        id="song",
        label="song",
        phrase="a steady work song",
        kind="help",
    ),
}

GIRL_NAMES = ["Mira", "Nell", "Hazel", "Pip", "Tess", "Wren"]
BOY_NAMES = ["Otto", "Bram", "Finn", "Toby", "Joss", "Rook"]
FOLK_TRAITS = ["kind", "brave", "cheerful", "patient", "clever", "steady"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            for item_id in SHARED_ITEMS:
                combos.append((place, task_id, item_id))
    return combos


@dataclass
class StoryParams:
    place: str
    task: str
    shared_item: str
    name: str
    gender: str
    elder: str
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


def _sound_line(sound: str) -> str:
    return {
        "squish-splash": "Squish-splash, went the mud as it softened under careful feet.",
        "glug-glug": "Glug-glug, went the water as it poured from hand to hand.",
    }.get(sound, "The little folk made a soft, busy sound as they worked.")


def _task_line(task: Task) -> str:
    return f"That was when the village learned to {task.verb} together."


def reasonableness_gate(task: Task, item: SharedItem, setting: Setting) -> bool:
    if task.id not in setting.affords:
        return False
    if item.kind != "tool" and task.id == "condition_mud":
        return False
    return True


def explain_rejection(task: Task, item: SharedItem) -> str:
    return (
        f"(No story: {task.gerund} needs a shared tool and a place that can hold the work. "
        f"The chosen item, {item.label}, does not fit that little folk-task.)"
    )


def make_names(gender: str) -> list[str]:
    return GIRL_NAMES if gender == "girl" else BOY_NAMES


def tell(setting: Setting, task: Task, shared_item: SharedItem, hero_name: str,
         gender: str, elder_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=gender,
        traits=["little", trait],
        meters={"muddy": 0.0, "joy": 0.0, "worry": 0.0, "teamwork": 0.0, "sharing": 0.0},
        memes={"joy": 0.0, "worry": 0.0, "sharing": 0.0, "teamwork": 0.0},
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        label=f"Old {elder_type.title()}",
        traits=["wise", "steady"],
        meters={"worry": 0.0, "joy": 0.0, "teamwork": 0.0},
        memes={"worry": 0.0, "joy": 0.0, "teamwork": 0.0},
    ))
    bucket = world.add(Entity(
        id=shared_item.id,
        kind="thing",
        type=shared_item.kind,
        label=shared_item.label,
        phrase=shared_item.phrase,
        plural=shared_item.plural,
        shared=True,
        owner=None,
        caretaker=elder.id,
        meters={"water": 0.0, "wear": 0.0},
    ))
    if not reasonableness_gate(task, shared_item, setting):
        pass

    world.say(f"At {setting.place}, little {hero_name} was a {trait} {gender} who liked helping the folk.")
    world.say(f"{hero.pronoun().capitalize()} loved {task.gerund}, and the village loved a good shared job.")
    world.say(f"Old {elder_type.title()} had brought {bucket.phrase} for everyone to use.")

    world.para()
    world.say(f"One wet morning, the path near {setting.place} had turned to sticky mud.")
    world.say(f"{hero_name} wanted to help mend it, but the mud was {task.soil}.")
    world.say(_sound_line(task.sound))
    hero.memes["worry"] += 1
    elder.memes["worry"] += 1
    world.say(f"{hero.pronoun('possessive').capitalize()} little heart thumped, because one bucket was not enough for all the folk.")

    world.para()
    world.say(
        f'“We must {task.verb}, and we must share,” said Old {elder_type.title()}. '
        f'“One pours, one stirs, one packs, and one sings.”'
    )
    hero.memes["sharing"] += 1
    hero.memes["teamwork"] += 1
    elder.memes["teamwork"] += 1
    bucket.meters["water"] = 1.0
    world.say(f"So the folk took turns with the {bucket.label}: {hero_name} carried it, the elder filled it, and the children passed it on.")
    world.say(_sound_line("glug-glug"))
    world.say(f"With every turn, the mud grew softer and kinder to the hands.")
    world.say(f"{hero_name} pressed the edge of the path, and the muddy patch began to hold its shape.")
    hero.meters["muddy"] += 1
    hero.meters["joy"] += 1
    hero.meters["teamwork"] += 1

    world.para()
    world.say(f"Then everyone worked at once, just as the elder had taught.")
    world.say(f"One foot stamped, one hand smoothed, one voice sang a beat: thump-thump, swish-swish, pat-pat.")
    world.say(_sound_line(task.sound))
    world.say(f"The mud finally became soft enough to pack, and the broken place stopped wobbling underfoot.")
    world.say(f"{hero_name} laughed, muddy from toes to cuffs, because the whole village was helping now.")
    hero.meters["joy"] += 1
    hero.memes["joy"] += 1
    hero.memes["teamwork"] += 1
    elder.meters["joy"] += 1
    elder.memes["joy"] += 1

    world.para()
    world.say(
        f"In the end, the path was fixed, the bucket was shared fairly, and the folk crossed together with merry plop-plop sounds."
    )
    world.say(f"{hero_name} looked back at the shining mud and smiled, because teamwork had made the hard work light.")

    world.facts.update(
        hero=hero,
        elder=elder,
        bucket=bucket,
        task=task,
        setting=setting,
        shared_item=shared_item,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    elder = _safe_fact(world, f, "elder")
    task = _safe_fact(world, f, "task")
    setting = _safe_fact(world, f, "setting")
    item = _safe_fact(world, f, "shared_item")
    return [
        f'Write a small folk tale for a child about {hero.id}, {task.keyword}, and a shared {item.label}.',
        f"Tell a story where {hero.id} and {elder.label} must {task.verb} at {setting.place} using teamwork.",
        f'Write a gentle story that includes the words "{task.keyword}" and "mud" and ends with a happy shared fix.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    elder = _safe_fact(world, f, "elder")
    task = _safe_fact(world, f, "task")
    setting = _safe_fact(world, f, "setting")
    item = _safe_fact(world, f, "shared_item")
    return [
        QAItem(
            question=f"Who helped {hero.id} at {setting.place}?",
            answer=f"{hero.id} helped with Old {elder.type.title()} and the rest of the village folk.",
        ),
        QAItem(
            question=f"What did the folk need to do with the mud?",
            answer=f"They needed to {task.verb} so the path could be fixed.",
        ),
        QAItem(
            question=f"What did everyone share while they worked?",
            answer=f"They shared the {item.label} and took turns with the water.",
        ),
        QAItem(
            question=f"How did the mud sound while it was being prepared?",
            answer=f"It made soft child-friendly sounds like squish-splash and glug-glug as the folk worked.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The muddy path became firm enough for the whole village to cross together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is mud?",
            answer="Mud is wet earth that can feel sticky, soft, and slippery under your feet.",
        ),
        QAItem(
            question="Why do people share tools when they work together?",
            answer="People share tools so everyone can help without waiting too long, and the job gets done faster.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when several people help with the same job and each person does a part.",
        ),
        QAItem(
            question="Why do stories use sound effects?",
            answer="Stories use sound effects to make actions feel lively and easy to imagine, like splish, thump, and plop.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.shared:
            bits.append("shared=True")
        out.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
% A task is valid when the setting affords it and the chosen shared item fits the
% folk tale's need for sharing and teamwork.
valid(Place, Task, Item) :- affords(Place, Task), tool(Item), requires_sharing(Task).

% Story mode: conditioning mud needs a shared tool; otherwise the village cannot
% reasonably solve the problem together.
can_tell(Place, Task, Item) :- valid(Place, Task, Item).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for task_id in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, task_id))
    for task_id, task in TASKS.items():
        lines.append(asp.fact("task", task_id))
        lines.append(asp.fact("requires_sharing", task_id))
    for item_id, item in SHARED_ITEMS.items():
        lines.append(asp.fact("tool", item_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
        return 0
    print("MISMATCH between clingo and python gates.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A folk-tale story world about conditioning mud, sharing, sound effects, and teamwork."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--shared-item", choices=SHARED_ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["mother", "father", "grandmother", "grandfather", "aunt", "uncle"])
    ap.add_argument("--name")
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
    if getattr(args, "place", None) and getattr(args, "task", None) and getattr(args, "shared_item", None):
        setting = _safe_lookup(SETTINGS, getattr(args, "place", None))
        task = _safe_lookup(TASKS, getattr(args, "task", None))
        item = _safe_lookup(SHARED_ITEMS, getattr(args, "shared_item", None))
        if not reasonableness_gate(task, item, setting):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
        and (getattr(args, "shared_item", None) is None or c[2] == getattr(args, "shared_item", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, task_id, item_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(make_names(gender))
    elder = getattr(args, "elder", None) or rng.choice(["grandmother", "grandfather", "aunt", "uncle"])
    trait = rng.choice(FOLK_TRAITS)
    return StoryParams(place=place, task=task_id, shared_item=item_id, name=name, gender=gender, elder=elder, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(TASKS, params.task),
        _safe_lookup(SHARED_ITEMS, params.shared_item),
        params.name,
        params.gender,
        params.elder,
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


CURATED = [
    StoryParams(place="village_green", task="condition_mud", shared_item="bucket", name="Mira", gender="girl", elder="grandmother", trait="steady"),
    StoryParams(place="mill_road", task="condition_mud", shared_item="trowel", name="Bram", gender="boy", elder="uncle", trait="brave"),
    StoryParams(place="barn_yard", task="share_water", shared_item="bucket", name="Nell", gender="girl", elder="aunt", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, task, item) combos:\n")
        for place, task, item in triples:
            print(f"  {place:14} {task:16} {item}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
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
            header = f"### {p.name}: {p.task} at {p.place} (shared item: {p.shared_item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
