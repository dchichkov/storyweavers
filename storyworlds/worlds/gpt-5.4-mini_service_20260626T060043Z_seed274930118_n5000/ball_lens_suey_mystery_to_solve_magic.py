#!/usr/bin/env python3
"""
ball_lens_suey_mystery_to_solve_magic.py
========================================

A small myth-style story world about a lost ball, a truth-revealing lens,
and a child who learns that magic can solve a mystery without breaking trust.

The core tale imagined from the seed:
---
In a village that loved old songs, a bright ball vanished at dusk.
Little Suey wanted to find it. An elder gave Suey a glass lens said to show
what ordinary eyes missed. The lens revealed tiny clues in the dust, and the
search led Suey past moonlit stones, a whispering tree, and a hidden hollow.
At the end, the ball was found, and the magic was used gently: not to command,
but to understand.
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
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    protective: bool = False
    magic: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    hero: object | None = None
    obj: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister", "elder"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother"}:
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
class Setting:
    name: str
    place: str
    moonlit: bool = False
    affords: set[str] = field(default_factory=set)
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


@dataclass
class ObjectDef:
    id: str
    label: str
    phrase: str
    type: str
    risk: str
    hint: str
    special: str = ""
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
class ToolDef:
    id: str
    label: str
    phrase: str
    reveals: set[str] = field(default_factory=set)
    wards: set[str] = field(default_factory=set)
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
class StoryParams:
    setting: str
    object: str
    tool: str
    hero_name: str
    hero_type: str
    elder_name: str
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
        self.clues: list[str] = []

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.clues = list(self.clues)
        return c


SETTINGS = {
    "hill": Setting(name="hill", place="on the moonlit hill", moonlit=True, affords={"seek", "reveal"}),
    "grove": Setting(name="grove", place="in the old grove", moonlit=False, affords={"seek", "reveal"}),
    "shore": Setting(name="shore", place="by the silver shore", moonlit=True, affords={"seek", "reveal"}),
}

OBJECTS = {
    "ball": ObjectDef(
        id="ball",
        label="ball",
        phrase="a bright ball of painted leather",
        type="ball",
        risk="lost",
        hint="its round shape left little prints in dust",
        special="It was the kind of ball that children named in songs.",
    ),
    "lens": ObjectDef(
        id="lens",
        label="lens",
        phrase="a small glass lens in a carved frame",
        type="lens",
        risk="hidden",
        hint="it could catch a clue that the naked eye missed",
        special="The lens was said to reveal what truth had tucked away.",
    ),
    "suey": ObjectDef(
        id="suey",
        label="suey",
        phrase="a curious child named Suey",
        type="child",
        risk="worried",
        hint="Suey listened closely when the elders spoke of signs",
        special="Suey had a brave heart and a soft voice.",
    ),
}

TOOLS = {
    "magic_lens": ToolDef(
        id="magic_lens",
        label="magic lens",
        phrase="the magic lens",
        reveals={"clue", "path", "hollow"},
        wards={"confusion"},
    ),
    "moon_spell": ToolDef(
        id="moon_spell",
        label="moon spell",
        phrase="a moon spell whispered by an elder",
        reveals={"clue", "path"},
        wards={"fear"},
    ),
}

GIRL_NAMES = ["Suey", "Mira", "Nia", "Lena", "Tali"]
BOY_NAMES = ["Orin", "Bren", "Kai", "Eli", "Jori"]
ELDER_NAMES = ["Old Mara", "Elder Sive", "Grand Toma", "Aunt Hira"]

CURATED = [
    StoryParams(setting="hill", object="ball", tool="magic_lens", hero_name="Suey", hero_type="girl", elder_name="Old Mara"),
    StoryParams(setting="grove", object="ball", tool="moon_spell", hero_name="Suey", hero_type="girl", elder_name="Elder Sive"),
    StoryParams(setting="shore", object="ball", tool="magic_lens", hero_name="Suey", hero_type="girl", elder_name="Aunt Hira"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Myth-style mystery story world about a lost ball, a lens, and magic.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--elder-name")
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for o in OBJECTS:
            for t in TOOLS:
                if o == "ball" and t in {"magic_lens", "moon_spell"}:
                    combos.append((s, o, t))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "object_", None) and getattr(args, "tool", None) and getattr(args, "object_", None) != "ball":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "object_", None) is None or c[1] == getattr(args, "object_", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, obj, tool = rng.choice(list(combos))
    hero_type = getattr(args, "hero_type", None) or "girl"
    hero_name = getattr(args, "hero_name", None) or ("Suey" if hero_type == "girl" else rng.choice(BOY_NAMES))
    elder_name = getattr(args, "elder_name", None) or rng.choice(ELDER_NAMES)
    return StoryParams(setting=setting, object=obj, tool=tool, hero_name=hero_name, hero_type=hero_type, elder_name=elder_name)


def narrate_intro(world: World, hero: Entity, elder: Entity, obj: Entity) -> None:
    world.say(
        f"Long ago, when the stars still learned their names, {hero.id} lived near {world.setting.place}."
    )
    world.say(
        f"{hero.id} loved the {obj.label}, and {obj.special.lower()}"
    )


def narrate_loss(world: World, hero: Entity, obj: Entity) -> None:
    hero.memes["worry"] = 1
    obj.meters["lost"] = 1
    world.say(
        f"One dusk the {obj.label} was gone, and the path looked empty where it had once flashed like a little sun."
    )


def narrate_request(world: World, hero: Entity, elder: Entity, tool: Entity) -> None:
    world.say(
        f"{hero.id} went to {elder.id} and asked for help. The elder placed {tool.phrase} in {hero.pronoun('possessive')} hands."
    )
    world.say(
        f'"Use it gently," {elder.id} said. "Magic can find what fear hides, but it must not frighten the thing you seek."'
    )


def narrate_search(world: World, hero: Entity, tool: Entity, obj: Entity) -> None:
    world.say(
        f"{hero.id} held {tool.phrase} to the moonlight and looked for signs."
    )
    world.clues.extend(["dust", "stone", "roots"])
    world.say(
        f"The glass caught a faint mark in the dust, then a little gleam by the stones, then a whisper under the roots."
    )


def narrate_find(world: World, hero: Entity, obj: Entity) -> None:
    obj.meters["found"] = 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(
        f"At last {hero.id} lifted a fern leaf, and there beneath it rested the {obj.label}, bright and whole."
    )


def narrate_end(world: World, hero: Entity, elder: Entity, obj: Entity, tool: Entity) -> None:
    world.say(
        f"{hero.id} returned the {tool.label} with a grateful bow, and {elder.id} smiled at the careful magic."
    )
    world.say(
        f"That night the village sang of how {hero.id} found the {obj.label} not by force, but by truth, patience, and a little light."
    )


def generate_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    elder = world.add(Entity(id=params.elder_name, kind="character", type="elder"))
    obj_def = _safe_lookup(OBJECTS, params.object)
    obj = world.add(Entity(id=obj_def.id, type=obj_def.type, label=obj_def.label, phrase=obj_def.phrase, owner=hero.id))
    tool_def = _safe_lookup(TOOLS, params.tool)
    tool = world.add(Entity(id=tool_def.id, type="tool", label=tool_def.label, phrase=tool_def.phrase, magic=True))

    narrate_intro(world, hero, elder, obj)
    world.para()
    narrate_loss(world, hero, obj)
    world.para()
    narrate_request(world, hero, elder, tool)
    narrate_search(world, hero, tool, obj)
    narrate_find(world, hero, obj)
    world.para()
    narrate_end(world, hero, elder, obj, tool)

    world.facts.update(hero=hero, elder=elder, obj=obj, tool=tool, obj_def=obj_def, tool_def=tool_def, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for a child about {f["hero"].id}, a lost {f["obj"].label}, and a {f["tool_def"].label}.',
        f"Tell a gentle legend in which {f['hero'].id} uses magic to solve a mystery and find a missing {f['obj'].label}.",
        f'Write a story with a moonlit mood where a clever lens reveals clues and the lost {f["obj"].label} is found.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    elder = _safe_fact(world, f, "elder")
    obj = _safe_fact(world, f, "obj")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"What mystery did {hero.id} need to solve?",
            answer=f"{hero.id} needed to solve the mystery of the missing {obj.label}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} with the search?",
            answer=f"{elder.id} helped {hero.id} and gave {hero.pronoun('object')} {tool.phrase}.",
        ),
        QAItem(
            question=f"How was the {obj.label} found?",
            answer=f"It was found by using {tool.phrase} to catch small clues and follow them carefully.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The {obj.label} was no longer lost, and {hero.id} felt glad and wise after the search.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lens used for?",
            answer="A lens helps you see things more clearly or notice small details that are hard to spot.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not understood yet and needs careful looking or thinking to solve.",
        ),
        QAItem(
            question="What is magic in stories?",
            answer="Magic in stories is a special kind of wonder that can reveal, change, or help things in unusual ways.",
        ),
        QAItem(
            question="What is a ball?",
            answer="A ball is a round object that can be rolled, tossed, or kicked in play.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.magic:
            bits.append("magic=True")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  clues: {world.clues}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- place(S).
object(O) :- item(O).
tool(T) :- instrument(T).

mystery_to_solve(S, O, T) :- setting(S), object(O), tool(T), O = ball, T = magic_lens.
mystery_to_solve(S, O, T) :- setting(S), object(O), tool(T), O = ball, T = moon_spell.

compatible(S, O, T) :- mystery_to_solve(S, O, T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("place", sid))
    for oid in OBJECTS:
        lines.append(asp.fact("item", oid))
    for tid in TOOLS:
        lines.append(asp.fact("instrument", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_sample(params: StoryParams) -> StorySample:
    world = generate_world(params)
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
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combinations:")
        for c in combos:
            print("  ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(build_sample(p))
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
            sample = build_sample(params)
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
            header = f"### {p.hero_name}: {p.object} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
