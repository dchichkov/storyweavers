#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/gentile_reconciliation_nursery_rhyme.py
===============================================================================================================

A small nursery-rhyme storyworld about a gentle misunderstanding and a
reconciliation.

Seed tale:
---
Two neighbors meet by a little gate. One child is Jewish, one is gentile.
They both love the same bouncing ball and the same bright song, but they
mistakenly think the other will not share. A parent helps them pause, talk,
and try again. They apologize, trade the ball, and end up singing together.

The simulated world tracks:
- physical meters: distance, possession, and shared objects
- emotional memes: worry, hurt, courage, and warmth

The story engine uses those state changes to tell a short, child-facing,
nursery-rhyme style tale with a clear reconciliation turn.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    plural: bool = False
    owner: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child_a_identity: object | None = None
    child_a: object | None = None
    child_b: object | None = None
    parent: object | None = None
    toy: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    place: str
    path: str
    rhyme_word: str
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
class Toy:
    id: str
    label: str
    phrase: str
    risk: str
    shelter: str
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
    setting: str = ""
    toy: str = ""
    child_a_name: str = ""
    child_a_type: str = ""
    child_a_identity: str = ""
    child_b_name: str = ""
    child_b_type: str = ""
    parent_type: str = ""
    seed: Optional[int] = None
    parent: object | None = None
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.events: list[str] = []

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


def _meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _mem(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = _meter(ent, key) + amount


def _add_mem(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = _mem(ent, key) + amount


def _clamp_nonnegative(ent: Entity, key: str) -> None:
    if ent.meters.get(key, 0.0) < 0:
        ent.meters[key] = 0.0
    if ent.memes.get(key, 0.0) < 0:
        ent.memes[key] = 0.0


def _do_worry(world: World, child: Entity, toy: Entity) -> None:
    _add_mem(child, "worry", 1.0)
    world.say(f"{child.id} clutched the {toy.label} and looked a little shy.")


def _do_misread(world: World, child: Entity, toy: Entity) -> None:
    _add_mem(child, "hurt", 1.0)
    _add_mem(child, "guarded", 1.0)
    world.say(f"{child.id} thought no one would share the {toy.label}, and {child.pronoun()} frowned.")


def _do_pause(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    _add_mem(a, "courage", 1.0)
    _add_mem(b, "courage", 1.0)
    world.say(f"{parent.pronoun('possessive').capitalize()} {parent.type} said, \"Pause now, dears, and breathe with me.\"")


def _do_apology(world: World, speaker: Entity, listener: Entity) -> None:
    _add_mem(speaker, "warmth", 1.0)
    _add_mem(speaker, "reconciliation", 1.0)
    _add_mem(listener, "warmth", 1.0)
    _add_mem(listener, "reconciliation", 1.0)
    _add_mem(listener, "hurt", -1.0)
    world.say(f"{speaker.id} said, \"I am sorry, my friend,\" and {listener.id} softened at once.")


def _do_share(world: World, a: Entity, b: Entity, toy: Entity) -> None:
    toy.held_by = a.id
    _add_meter(a, "possession", 1.0)
    _add_meter(b, "possession", 1.0)
    _add_mem(a, "joy", 1.0)
    _add_mem(b, "joy", 1.0)
    _add_mem(a, "reconciliation", 1.0)
    _add_mem(b, "reconciliation", 1.0)
    world.say(f"They took turns with the {toy.label}, one by one, in the sun by the gate.")


def _do_sing(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    _add_mem(a, "joy", 1.0)
    _add_mem(b, "joy", 1.0)
    world.say(f"Then they sang a tidy tune, and the little lane rang bright at {setting.place}.")


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    world = World(setting)

    child_a = world.add(Entity(
        id=params.child_a_name, kind="character", type=params.child_a_type,
        traits=["little", "gentile"] if params.child_a_identity == "gentile" else ["little", "jewish"],
    ))
    child_b = world.add(Entity(
        id=params.child_b_name, kind="character", type=params.child_b_type,
        traits=["little", "jewish"] if params.child_a_identity == "gentile" else ["little", "gentile"],
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_type, label="the parent"))
    toy = world.add(Entity(id=params.toy, kind="thing", type="toy", label=_safe_lookup(TOYS, params.toy).label, phrase=_safe_lookup(TOYS, params.toy).phrase))
    toy.held_by = child_a.id
    child_a.meters["possession"] = 1.0
    child_b.meters["distance"] = 1.0

    world.say(
        f"By {setting.place}, under a little blue sky, {child_a.id} met {child_b.id} at the gate."
    )
    world.say(
        f"One child was {child_a.traits[-1]}, and the other was {child_b.traits[-1]}; both loved the {toy.label}."
    )

    world.para()
    world.say(f"{child_a.id} had {toy.phrase}, and {child_b.id} wanted a turn with the same bright thing.")
    _do_worry(world, child_a, toy)
    _do_misread(world, child_b, toy)

    world.para()
    _do_pause(world, parent, child_a, child_b)
    _do_apology(world, child_a, child_b)
    _do_apology(world, child_b, child_a)
    _do_share(world, child_a, child_b, toy)
    _do_sing(world, child_a, child_b, setting)

    world.facts.update(
        child_a=child_a,
        child_b=child_b,
        parent=parent,
        toy=toy,
        setting=setting,
        reconciled=True,
    )
    return world


SETTINGS = {
    "gate": Setting(place="the little gate", path="lane", rhyme_word="bright"),
    "yard": Setting(place="the sunny yard", path="path", rhyme_word="day"),
    "bench": Setting(place="the bench by the willow", path="walk", rhyme_word="glow"),
}

TOYS = {
    "ball": Toy(
        id="ball",
        label="red ball",
        phrase="a red ball with a little bell",
        risk="bump",
        shelter="basket",
    ),
    "kite": Toy(
        id="kite",
        label="paper kite",
        phrase="a paper kite with a ribbon tail",
        risk="tear",
        shelter="porch",
    ),
    "drum": Toy(
        id="drum",
        label="small drum",
        phrase="a small drum with a shiny strap",
        risk="clang",
        shelter="blanket",
    ),
}

GENTILE_NAMES = ["Nora", "Mina", "Lena", "Theo", "Eli", "Milo", "Sara", "June"]
JEWISH_NAMES = ["Ruth", "Ada", "Noam", "Ira", "Leah", "Asher", "Maya", "Ezra"]
TRAITS = ["gentle", "cheerful", "curious", "patient", "spry"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for setting in SETTINGS:
        for toy in TOYS:
            combos.append((setting, toy))
    return combos


def explain_rejection(setting: str, toy: str) -> str:
    return f"(No story: {toy} does not fit the reconciliation scene at {setting}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld of gentile reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--identity-a", choices=["gentile", "jewish"])
    ap.add_argument("--child-a-type", choices=["girl", "boy"])
    ap.add_argument("--child-b-type", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if getattr(args, "setting", None) and getattr(args, "toy", None) and (getattr(args, "setting", None), getattr(args, "toy", None)) not in valid_combos():
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting = getattr(args, "setting", None) or rng.choice(sorted(SETTINGS))
    toy = getattr(args, "toy", None) or rng.choice(sorted(TOYS))
    identity_a = getattr(args, "identity_a", None) or rng.choice(["gentile", "jewish"])
    if identity_a == "gentile":
        name_a = getattr(args, "name_a", None) or rng.choice(GENTILE_NAMES)
        name_b = getattr(args, "name_b", None) or rng.choice(JEWISH_NAMES)
    else:
        name_a = getattr(args, "name_a", None) or rng.choice(JEWISH_NAMES)
        name_b = getattr(args, "name_b", None) or rng.choice(GENTILE_NAMES)
    return StoryParams(
        setting=setting,
        toy=toy,
        child_a_name=name_a,
        child_a_type=getattr(args, "child_a_type", None) or rng.choice(["girl", "boy"]),
        child_a_identity=identity_a,
        child_b_name=name_b,
        child_b_type=getattr(args, "child_b_type", None) or rng.choice(["girl", "boy"]),
        parent=getattr(args, "parent", None) or rng.choice(["mother", "father"]),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short nursery-rhyme story about gentile {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child_a").id} and {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child_b").id} sharing a {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "toy").label}.',
        f"Tell a gentle reconciliation tale at {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "setting").place} where a parent helps two children make up.",
        f'Write a rhyming story that includes the word "gentile" and ends with friends singing together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, parent, toy, setting = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child_a"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child_b"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "toy"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "setting")
    return [
        QAItem(
            question=f"Who met by {setting.place} and wanted the {toy.label}?",
            answer=f"{a.id} and {b.id} met by {setting.place}, and both wanted a turn with the {toy.label}.",
        ),
        QAItem(
            question=f"Why did {b.id} feel a little hurt at first?",
            answer=f"{b.id} felt hurt because {b.id} thought the {toy.label} would not be shared.",
        ),
        QAItem(
            question=f"How did the children fix the trouble?",
            answer=f"{parent.pronoun('possessive').capitalize()} {parent.type} asked them to pause, and then they apologized, shared the {toy.label}, and sang together.",
        ),
        QAItem(
            question=f"What was special about one child in this story?",
            answer=f"One child was gentile, and the story gently showed that gentile neighbors can be friends and reconcile kindly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making up after a disagreement so people can be kind to each other again.",
        ),
        QAItem(
            question="What is a nursery rhyme?",
            answer="A nursery rhyme is a short, simple song or poem with a playful beat and easy words for children.",
        ),
        QAItem(
            question="What does gentile mean?",
            answer="Gentile means a person who is not Jewish.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.kind == "character":
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


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


ASP_RULES = r"""
valid_story(S,T) :- setting(S), toy(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TOYS:
        lines.append(asp.fact("toy", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams("gate", "ball", "Nora", "girl", "gentile", "Ezra", "boy", "mother"),
    StoryParams("yard", "kite", "Ira", "boy", "jewish", "Mina", "girl", "father"),
    StoryParams("bench", "drum", "Lena", "girl", "gentile", "Noam", "boy", "mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            i += 1
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.child_a_name} and {p.child_b_name} at {p.setting} ({p.toy})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
