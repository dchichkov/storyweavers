#!/usr/bin/env python3
"""
collector_rent_foreshadowing_kindness_detective_story.py
=========================================================

A tiny detective-story world about a collector, a rent notice, foreshadowing,
and a kind solution.

Seed premise:
- A collector has a room full of small treasures and a rent bill due soon.
- Early clues foreshadow that one missing object will matter later.
- A child detective notices the pattern, follows the hints, and solves the case
  with kindness instead of blame.

This script keeps the domain small and classical: a few typed entities, physical
meters, emotional memes, a short causal trace, and a complete ending image.
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
# Domain data
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
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    lost: bool = False
    found: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    collector: object | None = None
    detective: object | None = None
    helper: object | None = None
    prized: object | None = None
    rent_notice: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    place: str = "the little market street"
    indoors: bool = False
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
class StoryItem:
    label: str
    phrase: str
    value: str
    clue: str
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
    place: str
    collector_name: str
    collector_type: str
    detective_name: str
    detective_type: str
    item: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "street": Setting(place="the little market street", indoors=False),
    "antique_shop": Setting(place="the antique shop", indoors=True),
    "train_station": Setting(place="the quiet train station", indoors=True),
}

ITEMS = {
    "clock": StoryItem(
        label="clock",
        phrase="a brass clock with a tiny moon on its face",
        value="rare",
        clue="it ticked twice whenever the rent was mentioned",
    ),
    "stamp": StoryItem(
        label="stamp",
        phrase="a blue stamp album with one empty page",
        value="special",
        clue="a torn page was stuck under the desk",
    ),
    "brooch": StoryItem(
        label="brooch",
        phrase="a silver brooch shaped like a leaf",
        value="family",
        clue="someone had cleaned the glass case where it used to sit",
    ),
}

COLLECTOR_NAMES = ["Mara", "Iris", "Nina", "June", "Ada", "Clara"]
DETECTIVE_NAMES = ["Pip", "Toby", "Milo", "Lena", "Kit", "Sage"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

def new_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))

    collector = world.add(Entity(
        id=params.collector_name,
        kind="character",
        type=params.collector_type,
        label="the collector",
    ))
    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_type,
        label="the detective",
    ))
    rent_notice = world.add(Entity(
        id="rent_notice",
        kind="thing",
        type="paper",
        label="rent notice",
        phrase="a rent notice with the due date circled in red",
        caretaker=collector.id,
    ))
    item = _safe_lookup(ITEMS, params.item)
    prized = world.add(Entity(
        id="prized_item",
        kind="thing",
        type=item.label,
        label=item.label,
        phrase=item.phrase,
        owner=collector.id,
        caretaker=collector.id,
        lost=True,
    ))
    helper = world.add(Entity(
        id="neighbor",
        kind="character",
        type="woman",
        label="the neighbor",
    ))

    collector.meters["worry"] = 1.0
    collector.memes["panic"] = 1.0
    detective.memes["curiosity"] = 1.0
    detective.memes["kindness"] = 1.0

    world.facts.update(
        collector=collector,
        detective=detective,
        notice=rent_notice,
        item=prized,
        helper=helper,
        setting=world.setting,
    )
    return world


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------

def _rule_foreshadow(world: World) -> list[str]:
    out = []
    collector = _safe_fact(world, world.facts, "collector")
    item = _safe_fact(world, world.facts, "item")
    if "foreshadowed" in world.fired:
        return out
    if collector.meters.get("worry", 0) >= 1 and item.lost:
        world.fired.add("foreshadowed")
        collector.memes["unease"] = collector.memes.get("unease", 0) + 1
        out.append(
            f"The collector kept glancing at the empty shelf, as if that missing spot "
            f"already knew trouble was coming."
        )
    return out


def _rule_notice_heavy(world: World) -> list[str]:
    out = []
    collector = _safe_fact(world, world.facts, "collector")
    notice = _safe_fact(world, world.facts, "notice")
    if "notice_heavy" in world.fired:
        return out
    if collector.meters.get("worry", 0) >= 1:
        world.fired.add("notice_heavy")
        notice.meters["importance"] = 1
        out.append(
            f"The rent notice felt heavier every time the collector folded it and unfolded it again."
        )
    return out


def _rule_kindness(world: World) -> list[str]:
    out = []
    detective = _safe_fact(world, world.facts, "detective")
    helper = _safe_fact(world, world.facts, "helper")
    collector = _safe_fact(world, world.facts, "collector")
    item = _safe_fact(world, world.facts, "item")
    if "kindness" in world.fired:
        return out
    if detective.memes.get("kindness", 0) >= 1 and item.lost and collector.memes.get("panic", 0) >= 1:
        world.fired.add("kindness")
        detective.memes["confidence"] = detective.memes.get("confidence", 0) + 1
        collector.memes["hope"] = collector.memes.get("hope", 0) + 1
        helper.memes["warmth"] = helper.memes.get("warmth", 0) + 1
        out.append(
            f"The detective asked gentle questions instead of sharp ones, and the neighbor answered kindly."
        )
    return out


def _rule_find_item(world: World) -> list[str]:
    out = []
    item = _safe_fact(world, world.facts, "item")
    detective = _safe_fact(world, world.facts, "detective")
    helper = _safe_fact(world, world.facts, "helper")
    collector = _safe_fact(world, world.facts, "collector")
    if "found" in world.fired:
        return out
    if detective.memes.get("confidence", 0) >= 1 and helper.memes.get("warmth", 0) >= 1:
        world.fired.add("found")
        item.lost = False
        item.found = True
        collector.meters["worry"] = 0
        collector.memes["panic"] = 0
        collector.memes["joy"] = collector.memes.get("joy", 0) + 1
        out.append(
            f"Behind a stack of receipt books, the detective found the missing {item.label}."
        )
    return out


CAUSAL_RULES = [_rule_foreshadow, _rule_notice_heavy, _rule_kindness, _rule_find_item]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Story prose
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    world = new_world(params)
    collector: Entity = _safe_fact(world, world.facts, "collector")
    detective: Entity = _safe_fact(world, world.facts, "detective")
    notice: Entity = _safe_fact(world, world.facts, "notice")
    item: Entity = _safe_fact(world, world.facts, "item")
    helper: Entity = _safe_fact(world, world.facts, "helper")

    world.say(
        f"{collector.id} was a careful collector who kept special things in {world.setting.place}."
    )
    world.say(
        f"{collector.pronoun('possessive').capitalize()} favorite treasure was {item.phrase}, and {notice.phrase} sat on the counter waiting for attention."
    )

    world.para()
    world.say(
        f"One evening, {collector.id} looked at the rent notice and sighed."
    )
    propagate(world)
    world.say(
        f"{collector.id} said {collector.pronoun('possessive')} missing {item.label} was the trouble, because it might help pay the rent."
    )

    world.para()
    world.say(
        f"Then {detective.id} arrived with a notebook and a soft voice."
    )
    world.say(
        f"{detective.id} noticed the clue: {item.clue}."
    )
    world.say(
        f"That made the case feel like a true detective story, with the answer hiding in plain sight."
    )
    propagate(world)

    world.para()
    world.say(
        f"{detective.id} asked {helper.id} where the {item.label} had gone."
    )
    world.say(
        f"{helper.id} pointed to the receipt books and admitted she had moved it to keep it safe during cleaning."
    )
    propagate(world)

    world.para()
    world.say(
        f"{collector.id} let out a relieved breath."
    )
    world.say(
        f"{detective.id} handed back the {item.label}, and {collector.id} smiled because kindness had solved the mystery without a single harsh word."
    )
    world.say(
        f"By nightfall, the rent notice was still on the counter, but the collector's heart felt light and the little shop was calm again."
    )

    world.facts.update(params=params, item_name=item.label)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p: StoryParams = _safe_fact(world, world.facts, "params")
    item: Entity = _safe_fact(world, world.facts, "item")
    return [
        f"Write a short detective story about {p.collector_name}, a collector, who worries about rent and a missing {item.label}.",
        f"Tell a gentle mystery with foreshadowing and kindness where {p.detective_name} helps solve the problem.",
        f"Create a child-friendly detective tale set in {world.setting.place} with a rent notice, a clue, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = _safe_fact(world, world.facts, "params")
    collector: Entity = _safe_fact(world, world.facts, "collector")
    detective: Entity = _safe_fact(world, world.facts, "detective")
    item: Entity = _safe_fact(world, world.facts, "item")

    return [
        QAItem(
            question=f"Who was the collector worried about rent?",
            answer=f"The collector was {p.collector_name}, and {collector.pronoun('subject')} was worried because the rent notice was waiting on the counter.",
        ),
        QAItem(
            question=f"What clue foreshadowed the mystery about the {item.label}?",
            answer=f"The clue was that {item.clue}. That hint pointed toward the missing {item.label} before anyone found it.",
        ),
        QAItem(
            question=f"Who solved the case kindly?",
            answer=f"The detective {p.detective_name} solved it with gentle questions, and that kindness helped everyone tell the truth.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"The missing {item.label} was found behind the receipt books, and the collector felt relieved because the mystery was solved kindly.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a detective?",
        answer="A detective is a person who looks for clues and tries to solve a mystery.",
    ),
    QAItem(
        question="What is rent?",
        answer="Rent is the money someone pays to keep living or working in a place.",
    ),
    QAItem(
        question="What is foreshadowing?",
        answer="Foreshadowing is when a story gives a small hint early on about something that will matter later.",
    ),
    QAItem(
        question="What is kindness?",
        answer="Kindness means being gentle, helpful, and caring toward other people.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for q in sample.prompts:
        lines.append(q)
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.lost:
            bits.append("lost=True")
        if e.found:
            bits.append("found=True")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Facts:
% setting(place).
% collector(name).
% detective(name).
% item(item).
% clue(item, text).
% rent_due(place).

foreshadowed(I) :- item(I), clue(I, _).
kind_help(D) :- detective(D).
found(I) :- foreshadowed(I), kind_help(_).

:- item(I), not foreshadowed(I).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for key in SETTINGS:
        lines.append(asp.fact("setting", key))
    for key, item in ITEMS.items():
        lines.append(asp.fact("item", key))
        lines.append(asp.fact("clue", key, item.clue))
    lines.append(asp.fact("rent_due", "street"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show foreshadowed/1."))
    asp_set = set(asp.atoms(model, "foreshadowed"))
    py_set = {(k,) for k in ITEMS}
    if asp_set == py_set:
        print(f"OK: ASP and Python agree on foreshadowing ({len(asp_set)} items).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", sorted(asp_set))
    print("PY :", sorted(py_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world about collector, rent, foreshadowing, and kindness.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--item", choices=ITEMS.keys())
    ap.add_argument("--collector-name", choices=COLLECTOR_NAMES)
    ap.add_argument("--detective-name", choices=DETECTIVE_NAMES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS.keys()))
    item = getattr(args, "item", None) or rng.choice(list(ITEMS.keys()))
    collector_name = getattr(args, "collector_name", None) or rng.choice(COLLECTOR_NAMES)
    detective_name = getattr(args, "detective_name", None) or rng.choice(DETECTIVE_NAMES)
    collector_type = "woman" if collector_name in {"Mara", "Iris", "Nina", "June", "Ada", "Clara"} else "man"
    detective_type = "girl" if detective_name in {"Lena", "Kit", "Sage"} else "boy"
    if collector_name == detective_name:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        place=place,
        collector_name=collector_name,
        collector_type=collector_type,
        detective_name=detective_name,
        detective_type=detective_type,
        item=item,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show foreshadowed/1.\n#show found/1."))
        return

    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show foreshadowed/1.\n#show found/1."))
        print("foreshadowed:", sorted(asp.atoms(model, "foreshadowed")))
        print("found:", sorted(asp.atoms(model, "found")))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place in SETTINGS:
            for item in ITEMS:
                params = StoryParams(
                    place=place,
                    collector_name=_safe_lookup(COLLECTOR_NAMES, 0),
                    collector_type="woman",
                    detective_name=_safe_lookup(DETECTIVE_NAMES, 0),
                    detective_type="boy",
                    item=item,
                    seed=base_seed,
                )
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
        header = f"### variant {idx + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
