#!/usr/bin/env python3
"""
storyworlds/worlds/reindeer_delicious_minimize_twist_cautionary_folk_tale.py
============================================================================

A standalone story world for a small folk-tale domain about a reindeer, a
delicious temptation, and a cautious twist that teaches a child-sized lesson.

Seed tale:
---
Long ago, in a snowy village, a young reindeer named Suri loved to help the
baker carry berries across the hill. One winter morning, Suri found a shiny
sugar cake left on a cart. It smelled delicious. Suri wanted to eat it at once,
but the baker's old fox warned that too much sweet cake would make Suri's belly
ache and slow the sleigh.

Suri was tempted, then careful. Instead of gobbling the whole cake, Suri carried
it home and shared it with the winter birds, keeping only a tiny crumb. The fox
smiled, and the sleigh still flew.

Causal state updates:
---
    sweet smell nearby          -> reindeer desire += 1
    eating too much cake        -> reindeer tummy_ache += 1, speed -= 1
    sharing and keeping a crumb -> desire -= 1, joy += 1, greed -= 1

Scripted beats:
---
    folk tale setup             -> introduce village, reindeer, helper
    delicious twist offered     -> temptation rises
    cautionary warning          -> helper predicts consequence
    careful turn                -> reindeer minimizes the sweet
    resolution                  -> shared crumb, safe ending image
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    deer: object | None = None
    fox: object | None = None
    sweet: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"reindeer", "he", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
        if not hasattr(self, "_tags"):
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
    name: str
    snowy: bool = True
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Treat:
    id: str
    label: str
    phrase: str
    delicious: str
    risk: str
    small_share: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Helper:
    id: str
    label: str
    warning: str
    twist: str
    fix: str
    tags: set[str] = field(default_factory=set)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.snow: float = 0.0

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.snow = self.snow
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    CAUSAL_RULES: list = field(default_factory=list)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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


def _r_tummy(world: World) -> list[str]:
    out: list[str] = []
    deer = world.get("reindeer")
    treat = world.get("treat")
    if deer.meters["too_much_sweet"] < THRESHOLD:
        return out
    sig = ("tummy",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    deer.meters["tummy_ache"] += 1
    deer.meters["speed"] -= 1
    out.append(f"{deer.label} felt a tummy-ache and moved slower.")
    return out


def _r_sharing(world: World) -> list[str]:
    deer = world.get("reindeer")
    if deer.meters["shared"] < THRESHOLD:
        return []
    sig = ("share",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    deer.memes["joy"] += 1
    deer.memes["greed"] -= 1
    deer.memes["desire"] -= 1
    return ["__shared__"]


CAUSAL_RULES = [Rule("tummy", "physical", _r_tummy), Rule("share", "social", _r_sharing)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__shared__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sweet_at_risk(treat: Treat) -> bool:
    return True


def pick_valid_combos() -> list[tuple[str, str, str]]:
    return [(p, t, h) for p in PLACES for t in TREATS for h in HELPERS if sweet_at_risk(_safe_lookup(TREATS, t))]


@dataclass
class StoryParams:
    place: str
    treat: str
    helper: str
    name: str
    tone: str
    seed: Optional[int] = None
    samples: list = field(default_factory=list)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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


def setup_world(place: Place, treat: Treat, helper: Helper, name: str, tone: str) -> World:
    w = World(place)
    deer = w.add(Entity(id="reindeer", kind="character", type="reindeer", label=name, role="hero"))
    fox = w.add(Entity(id="helper", kind="character", type="fox", label=helper.label, role="helper"))
    sweet = w.add(Entity(id="treat", type="treat", label=treat.label, phrase=treat.phrase))
    w.facts.update(reindeer=deer, helper=fox, treat=sweet, place=place, treat_cfg=treat, helper_cfg=helper, tone=tone)
    deer.memes["desire"] = 0
    deer.memes["joy"] = 0
    deer.memes["greed"] = 0
    deer.meters["speed"] = 2
    deer.meters["tummy_ache"] = 0
    deer.meters["too_much_sweet"] = 0
    deer.meters["shared"] = 0
    fox.memes["caution"] = 1
    fox.meters["warned"] = 0
    return w


def predict(world: World) -> bool:
    sim = world.copy()
    deer = sim.get("reindeer")
    deer.meters["too_much_sweet"] = 1
    propagate(sim, narrate=False)
    return sim.get("reindeer").meters["tummy_ache"] >= THRESHOLD


def tell(place: Place, treat: Treat, helper: Helper, name: str, tone: str) -> World:
    w = setup_world(place, treat, helper, name, tone)
    deer = w.get("reindeer")
    fox = w.get("helper")
    sweet = w.get("treat")

    w.say(f"Long ago, in {place.name}, there lived a young reindeer named {deer.label}.")
    w.say(f"{deer.label} loved helping carry berries across the hill, and the snow made every hoofstep soft.")
    w.para()
    w.say(f"One winter morning, {deer.label} found {sweet.phrase} on a cart.")
    w.say(f"It smelled {treat.delicious}, and {deer.pronoun().capitalize()} wanted to taste it at once.")

    if predict(w):
        fox.meters["warned"] = 1
        w.say(f'But {fox.label} said, "{helper.warning}"')
        w.say(f'"{helper.twist}" {fox.label} added, looking at the cake with careful eyes.')
        w.para()
        deer.memes["desire"] += 1
        deer.meters["too_much_sweet"] += 1
        w.say(f"{deer.label} paused, then chose to minimize the sweet and keep only a tiny crumb.")
        w.say(f'{deer.label} shared the rest with the winter birds, just as {helper.fix}.')
        deer.meters["shared"] += 1
        propagate(w)
        w.para()
        w.say(f"In the end, {deer.label} trotted home with a light belly, a warm heart, and a crumb-sized smile.")
    else:
        deer.meters["too_much_sweet"] += 1
        w.say(f"{deer.label} ignored the warning and gobbled the whole treat.")
        propagate(w)
        w.para()
        w.say(f"That was too much sweet for one small reindeer, and the day grew slow and sticky.")

    w.facts["resolved"] = deer.meters["shared"] >= THRESHOLD
    w.facts["cautionary"] = True
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale for a child about a reindeer named {f["reindeer"].label} and a {f["treat_cfg"].label}.',
        f'Tell a cautionary story where a reindeer finds something {f["treat_cfg"].delicious} and learns to minimize the sweet.',
        f'Write a gentle tale with a twist where {f["helper_cfg"].label} warns about too much cake, and the ending stays warm and safe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    deer, helper, treat = f["reindeer"], f["helper"], f["treat"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {deer.label}, a young reindeer who loves helping and learns a careful lesson.",
        ),
        QAItem(
            question=f"What did {deer.label} find on the cart?",
            answer=f"{deer.label} found {treat.phrase}, and it smelled {treat.delicious}.",
        ),
        QAItem(
            question=f"What did {helper.label} warn about?",
            answer=f"{helper.label} warned that too much sweet cake would bring {treat.risk}.",
        ),
        QAItem(
            question=f"How did {deer.label} respond to the warning?",
            answer=f"{deer.label} chose to minimize the sweet, shared the rest, and kept only a tiny crumb.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="Why should you not eat too much cake?", answer="Too much cake can give you a belly ache and make you feel slow."),
        QAItem(question="What does it mean to share food?", answer="Sharing food means giving some to others instead of keeping it all for yourself."),
        QAItem(question="What is a cautionary story?", answer="A cautionary story teaches a safe lesson by showing what might go wrong if you are careless."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


PLACES = {
    "village": Place("the snowy village"),
    "hill": Place("the windy hill"),
    "barn": Place("the red barn"),
}

TREATS = {
    "cake": Treat("cake", "sugar cake", "a sugar cake", "delicious", "a belly ache", "a tiny crumb", {"sweet", "cake"}),
    "pie": Treat("pie", "berry pie", "a berry pie", "delicious", "a belly ache", "a tiny slice", {"sweet", "pie"}),
    "honey": Treat("honey", "honey tart", "a honey tart", "delicious", "a sticky tummy", "a tiny lick", {"sweet", "honey"}),
}

HELPERS = {
    "fox": Helper("fox", "old fox", "Too much sweet will make your belly ache.", "A tiny taste is wiser than a full bite.", "keep only a tiny crumb", {"caution", "twist"}),
    "owl": Helper("owl", "wise owl", "Take only a little, or the day will turn heavy.", "The smallest bite can still be kind.", "share the rest with the birds", {"caution", "twist"}),
    "goat": Helper("goat", "barn goat", "Too much sugar makes even a happy hoof feel slow.", "Minimize the sweet and keep the song.", "save most of it for later", {"caution", "twist"}),
}

NAMES = ["Suri", "Mika", "Tova", "Nell", "Pip", "Runa", "Lumi", "Bram"]


def valid_combos() -> list[tuple[str, str, str]]:
    return pick_valid_combos()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world about a reindeer, a delicious temptation, and a cautious twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--tone", default="folk")
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
              and (getattr(args, "treat", None) is None or c[1] == getattr(args, "treat", None))
              and (getattr(args, "helper", None) is None or c[2] == getattr(args, "helper", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, treat, helper = rng.choice(list(combos))
    return StoryParams(
        place=place,
        treat=treat,
        helper=helper,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        tone=getattr(args, "tone", None),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(TREATS, params.treat), _safe_lookup(HELPERS, params.helper), params.name, params.tone)
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
valid(P,T,H) :- place(P), treat(T), helper(H).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t in TREATS:
        lines.append(asp.fact("treat", t))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
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
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid_combos())
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(StoryParams(place=p, treat=t, helper=h, name=_safe_lookup(NAMES, i % len(NAMES)), tone=getattr(args, "tone", None))) for i, (p, t, h) in enumerate(valid_combos())]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
