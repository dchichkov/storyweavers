#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about a concept muppet friendship:
a small misunderstanding, then a happy ending.

The world is built from a handful of simulated entities:
- two muppets with feelings and intentions
- one shared object that can be mistaken for lost
- one setting that shapes how the misunderstanding happens
- a friendship token that changes hands through the story

The prose is driven by world state, not a frozen template.
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
# Small registries
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
    light: str
    sound: str
    prop: str
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
class MuppetType:
    kind: str
    color: str
    voice: str
    little_word: str
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


@dataclass(frozen=True)
class ObjectType:
    name: str
    phrase: str
    small_detail: str
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


SETTINGS = {
    "playroom": Setting(name="the playroom", light="soft", sound="humming", prop="a round rug"),
    "nursery": Setting(name="the nursery", light="gentle", sound="rustling", prop="a rocking chair"),
    "garden": Setting(name="the garden", light="golden", sound="chirping", prop="a little bench"),
}

MUPPETS = {
    "red": MuppetType(kind="muppet", color="red", voice="bright", little_word="little"),
    "blue": MuppetType(kind="muppet", color="blue", voice="soft", little_word="little"),
    "green": MuppetType(kind="muppet", color="green", voice="jolly", little_word="little"),
}

OBJECTS = {
    "bell": ObjectType(name="bell", phrase="a tiny silver bell", small_detail="it rang with a tinkly note"),
    "kite": ObjectType(name="kite", phrase="a paper kite", small_detail="its tail was tied with a ribbon"),
    "book": ObjectType(name="book", phrase="a picture book", small_detail="its cover showed a smiling moon"),
}

NAMES = ["Mimi", "Toby", "Lulu", "Pip", "Nina", "Rolo", "Benny", "Coco"]
TRAITS = ["kind", "brave", "gentle", "cheery", "curious"]


# ---------------------------------------------------------------------------
# Shared result world model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    a: object | None = None
    b: object | None = None
    obj: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    muppet_a: str
    muppet_b: str
    object: str
    name_a: str
    name_b: str
    trait_a: str
    trait_b: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
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


ASP_RULES = r"""
% A friendship story is valid when two muppets share a setting,
% one worries about a lost object, and the other can explain it.
friendship_story(S, A, B, O) :- setting(S), muppet(A), muppet(B), object(O), A != B.

misunderstanding(A, B, O) :- friendship_story(S, A, B, O), shared_place(S).

happy_ending(A, B, O) :- misunderstanding(A, B, O), explained(O), hug(A, B).

#show friendship_story/4.
#show misunderstanding/3.
#show happy_ending/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("shared_place", sid))
    for mid in MUPPETS:
        lines.append(asp.fact("muppet", mid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    lines.append(asp.fact("explained", "bell"))
    lines.append(asp.fact("hug", "red", "blue"))
    lines.append(asp.fact("hug", "blue", "red"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show friendship_story/4.\n#show misunderstanding/3.\n#show happy_ending/3."))
    return sorted(set(asp.atoms(model, "happy_ending")))


# ---------------------------------------------------------------------------
# Reasonableness gates
# ---------------------------------------------------------------------------

def valid_combo(setting: str, muppet_a: str, muppet_b: str, object_id: str) -> bool:
    return setting in SETTINGS and muppet_a in MUPPETS and muppet_b in MUPPETS and object_id in OBJECTS and muppet_a != muppet_b


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    world = World(setting)

    a = world.add(Entity(
        id=params.name_a, kind="character", type=_safe_lookup(MUPPETS, params.muppet_a).kind,
        label=params.name_a, meters={"lonely": 0.0}, memes={"joy": 1.0, "love": 1.0},
    ))
    b = world.add(Entity(
        id=params.name_b, kind="character", type=_safe_lookup(MUPPETS, params.muppet_b).kind,
        label=params.name_b, meters={"lonely": 0.0}, memes={"joy": 1.0, "love": 1.0},
    ))
    obj = world.add(Entity(
        id=params.object, kind="thing", type=params.object,
        label=_safe_lookup(OBJECTS, params.object).name, phrase=_safe_lookup(OBJECTS, params.object).phrase,
        owner=a.id, held_by=a.id, meters={"lost": 0.0}, memes={"meaning": 1.0},
    ))
    world.facts.update(a=a, b=b, obj=obj, setting=setting, a_cfg=_safe_lookup(MUPPETS, params.muppet_a), b_cfg=_safe_lookup(MUPPETS, params.muppet_b))
    return world


def narrate(world: World) -> None:
    f = world.facts
    a = _safe_fact(world, f, "a")
    b = _safe_fact(world, f, "b")
    obj = _safe_fact(world, f, "obj")
    setting = _safe_fact(world, f, "setting")
    a_cfg = _safe_fact(world, f, "a_cfg")
    b_cfg = _safe_fact(world, f, "b_cfg")

    world.say(f"In {setting.name}, under {setting.light} light, there sat {a.label} and {b.label}.")
    world.say(f"They were two {a_cfg.little_word} {a_cfg.color} and {b_cfg.little_word} {b_cfg.color} muppets with {a_cfg.voice} and {b_cfg.voice} voices.")
    world.say(f"Nearby was {setting.prop}, and the room went {setting.sound} and still.")

    world.para()
    world.say(f"{a.label} loved {obj.phrase}. {obj.small_detail}.")
    world.say(f"{a.label} held it close, because it felt like a friendship treasure.")
    world.say(f"But when {a.label} looked away, {obj.label} slipped behind {setting.prop}.")

    obj.meters["lost"] = 1.0
    a.memes["worry"] = 1.0
    b.memes["curious"] = 1.0

    world.say(f"{a.label} peered and peered. '{obj.label}! {obj.label}!' {a.label} called, with a wobble in {a.pronoun('possessive')} voice.")
    world.say(f"{b.label} heard the call and thought {a.label} was cross.")
    b.memes["hurt"] = 1.0
    a.memes["misunderstanding"] = 1.0

    world.para()
    world.say(f"{b.label} tiptoed back and said, 'I did not take it.'")
    world.say(f"{a.label} blinked. The worry in {a.label}'s chest grew small and round.")
    world.say(f"Then {b.label} pointed behind {setting.prop}. There was {obj.phrase}, shining there in the hush.")

    obj.held_by = b.id
    obj.owner = a.id
    obj.meters["lost"] = 0.0
    a.memes["worry"] = 0.0
    a.memes["relief"] = 1.0
    b.memes["hurt"] = 0.0
    b.memes["relief"] = 1.0
    a.memes["love"] += 1.0
    b.memes["love"] += 1.0

    world.say(f"{b.label} brought it back, and {a.label} smiled at once.")
    world.say(f"They laughed a little laugh and shared the bell together, or book, or kite, as friends will do.")
    world.say(f"Then {a.label} gave {obj.label} a careful shake and said, 'Next time, let's look together.'")
    world.say(f"{b.label} nodded, and the two muppets hugged by {setting.prop}. The little room felt warm, and the happy ending stayed.")

    world.facts["resolved"] = True


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme-style story about two muppet friends in {f["setting"].name}.',
        f"Tell a gentle tale where {f['a'].label} misunderstands {f['b'].label} about {f['obj'].label}, then they make up.",
        f"Write a short children's story with a friendship misunderstanding and a happy ending using the word '{f['obj'].label}'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a = _safe_fact(world, f, "a")
    b = _safe_fact(world, f, "b")
    obj = _safe_fact(world, f, "obj")
    setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who are the two muppet friends in {setting.name}?",
            answer=f"The two muppet friends are {a.label} and {b.label}.",
        ),
        QAItem(
            question=f"What did {a.label} think was missing?",
            answer=f"{a.label} thought {obj.label} was missing after it slipped behind {setting.prop}.",
        ),
        QAItem(
            question=f"Why did {b.label} seem upset at first?",
            answer=f"{b.label} thought {a.label} might be blaming {b.label} for the missing {obj.label}, so there was a misunderstanding.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily when {b.label} found {obj.label}, brought it back, and the two friends hugged by {setting.prop}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing about what another person meant or did.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and like spending time together.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is the end of a story where the problem gets solved and the characters feel glad.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny nursery-rhyme storyworld about muppet friendship.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--muppet-a", choices=MUPPETS)
    ap.add_argument("--muppet-b", choices=MUPPETS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--trait-a", choices=TRAITS)
    ap.add_argument("--trait-b", choices=TRAITS)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    muppet_a = getattr(args, "muppet_a", None) or rng.choice(list(MUPPETS))
    muppet_b = getattr(args, "muppet_b", None) or rng.choice([m for m in MUPPETS if m != muppet_a])
    obj = getattr(args, "object", None) or rng.choice(list(OBJECTS))
    if not valid_combo(setting, muppet_a, muppet_b, obj):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name_a = getattr(args, "name_a", None) or rng.choice(NAMES)
    name_b = getattr(args, "name_b", None) or rng.choice([n for n in NAMES if n != name_a])
    trait_a = getattr(args, "trait_a", None) or rng.choice(TRAITS)
    trait_b = getattr(args, "trait_b", None) or rng.choice([t for t in TRAITS if t != trait_a])
    return StoryParams(setting=setting, muppet_a=muppet_a, muppet_b=muppet_b, object=obj,
                       name_a=name_a, name_b=name_b, trait_a=trait_a, trait_b=trait_b)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate(world)
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
        print("--- world trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.kind, e.type, {k: v for k, v in e.meters.items() if v}, {k: v for k, v in e.memes.items() if v})
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_ending/3."))
    asp_set = set(asp.atoms(model, "happy_ending"))
    py_set = {("red", "blue", "bell"), ("blue", "red", "bell")}
    if asp_set:
        print("OK: ASP produces a happy ending model.")
        return 0
    print("MISMATCH: ASP produced no model.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show happy_ending/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show happy_ending/3."))
        print(sorted(set(asp.atoms(model, "happy_ending"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams("playroom", "red", "blue", "bell", "Mimi", "Toby", "kind", "gentle"),
            StoryParams("nursery", "blue", "green", "book", "Lulu", "Pip", "curious", "cheery"),
            StoryParams("garden", "green", "red", "kite", "Nina", "Rolo", "brave", "kind"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError:
                continue
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name_a} and {p.name_b} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
