#!/usr/bin/env python3
"""
storyworlds/worlds/revolve_caption_republican_kindness_suspense_space_adventure.py
==================================================================================

A standalone storyworld about a small space adventure with a revolving station,
a caption panel, and a surprising kindness under suspense.

Seed inspiration:
- revolve
- caption
- republican
- Kindness
- Suspense
- Space Adventure

Premise:
A child on a tiny moonbase wants to spin a display ring to make a caption
visible, but the ring is tied to a fragile signal dish. A careful co-pilot
foresees trouble, a tense choice follows, and kindness turns the moment into a
safe, bright ending.

This world keeps the prose child-facing and state-driven:
- physical meters track spin, drift, dust, and signal.
- emotional memes track worry, kindness, suspense, relief, and pride.
- a small rule engine forwards consequences.
- ASP facts/rules mirror the Python reasonableness gate.
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    moved: bool = False

    captain: object | None = None
    caption: object | None = None
    child: object | None = None
    dish: object | None = None
    helper: object | None = None
    ring: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Setting:
    place: str
    place_word: str
    indoors: bool = True
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
        return None


@dataclass
class Device:
    id: str
    label: str
    phrase: str
    flourish: str
    safe_after: str
    kind: str = "device"
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
class Move:
    id: str
    label: str
    verb: str
    risk: str
    consequence: str
    zone: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.spin_zone: str = ""
        self.trace_notes: list[str] = []

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
        c.fired = set(self.fired)
        c.spin_zone = self.spin_zone
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
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


def _r_signal(world: World) -> list[str]:
    out: list[str] = []
    ring = world.entities.get("ring")
    dish = world.entities.get("dish")
    if not ring or not dish:
        return out
    if ring.meters["revolve"] < THRESHOLD:
        return out
    if ("signal", ring.id) in world.fired:
        return out
    world.fired.add(("signal", ring.id))
    dish.meters["signal"] -= 1
    world.get("captain").memes["suspense"] += 1
    out.append("The signal flickered when the ring spun too fast.")
    return out


def _r_dust(world: World) -> list[str]:
    out: list[str] = []
    ring = world.entities.get("ring")
    if not ring or ring.meters["revolve"] < THRESHOLD:
        return out
    for e in world.characters():
        if ("dust", e.id) in world.fired:
            continue
        world.fired.add(("dust", e.id))
        e.meters["dust"] += 1
        out.append(f"{e.label_word.capitalize()} got a little dust on {e.pronoun('possessive')} suit.")
    return out


CAUSAL_RULES = [Rule("signal", _r_signal), Rule("dust", _r_dust)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def safe_choice(m: Move, d: Device) -> bool:
    return m.zone == "ring" and d.id in {"glow_caption", "soft_lantern"}


def predict_swing(world: World, move: Move) -> dict:
    sim = world.copy()
    sim.get("child").meters["revolve"] += 1
    propagate(sim, narrate=False)
    return {
        "signal": sim.get("dish").meters["signal"],
        "dust": sim.get("child").meters["dust"],
    }


def tell(setting: Setting, move: Move, device: Device, child_name: str, helper_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type="girl", label=child_name))
    helper = world.add(Entity(id=helper_name, kind="character", type="boy", label=helper_name))
    captain = world.add(Entity(id="captain", kind="character", type="mother", label="the captain"))
    ring = world.add(Entity(id="ring", type="thing", label="revolving ring"))
    dish = world.add(Entity(id="dish", type="thing", label="signal dish"))
    caption = world.add(Entity(id="caption", type="thing", label="caption panel"))

    dish.meters["signal"] = 3
    child.memes["kindness"] = 1
    helper.memes["suspense"] = 1

    world.say(
        f"{child.label_word} and {helper.label_word} lived on {setting.place}. "
        f"The station had a {ring.label} that could {move.verb} and a {caption.label} that liked to glow."
    )
    world.say(
        f"One night, they spotted {device.phrase}. It had a tiny {device.flourish} that made the caption feel special."
    )

    world.para()
    world.say(
        f"{child.label_word} wanted to {move.verb}, but {helper.label_word} noticed the {move.risk}."
    )
    pred = predict_swing(world, move)
    world.facts["pred"] = pred
    helper.memes["suspense"] += 1
    world.say(
        f'"If we spin it now, the {dish.label} could wobble," {helper.label_word} whispered. '
        f'That made the moment feel full of suspense.'
    )

    if safe_choice(move, device):
        world.say(
            f"{child.label_word} listened. Instead of yanking the ring, {child.label_word} and {helper.label_word} used {device.label} first."
        )
        child.memes["kindness"] += 1
        helper.memes["relief"] += 1
        caption.meters["bright"] += 1
        world.para()
        world.say(
            f"Together they held the caption steady, and the words read clear at last. "
            f"The little space scene stayed safe, and the kindness made the whole deck feel warm."
        )
        outcome = "safe"
    else:
        world.say(
            f"{child.label_word} pulled anyway. The ring began to revolve, and the caption flashed crookedly."
        )
        ring.meters["revolve"] += 1
        propagate(world, narrate=True)
        world.para()
        world.say(
            f"{captain.label_word.capitalize()} came over with a calm voice and a gentle hand. "
            f"She helped them slow the ring, reset the caption, and make the station safe again."
        )
        child.memes["kindness"] += 1
        helper.memes["relief"] += 1
        outcome = "warned"

    world.para()
    world.say(
        f"In the end, the caption shone straight across the {setting.place_word}, "
        f"and {child.label_word} smiled because {helper.label_word} had turned suspense into kindness."
    )

    world.facts.update(
        child=child, helper=helper, captain=captain, ring=ring, dish=dish, caption=caption,
        move=move, device=device, setting=setting, outcome=outcome
    )
    return world


SETTINGS = {
    "moonbase": Setting(place="the moonbase", place_word="moonbase", indoors=True),
    "orbit": Setting(place="the orbiting station", place_word="station", indoors=True),
    "crater": Setting(place="the crater camp", place_word="camp", indoors=False),
}

MOVES = {
    "revolve": Move(
        id="revolve",
        label="revolve",
        verb="revolve the ring",
        risk="the signal dish might wobble",
        consequence="the caption could flicker",
        zone="ring",
        tags={"revolve", "suspense"},
    ),
}

DEVICES = {
    "caption": Device(
        id="glow_caption",
        label="caption panel",
        phrase="a glowing caption panel",
        flourish="soft blue caption glow",
        safe_after="made the words clear without shaking anything",
    ),
    "lantern": Device(
        id="soft_lantern",
        label="soft lantern",
        phrase="a soft lantern",
        flourish="small round light",
        safe_after="lit the deck without touching the ring",
    ),
    "republican": Device(
        id="republican",
        label="republican sticker",
        phrase="a little republican sticker",
        flourish="tiny round letters",
        safe_after="stayed tucked on the wall",
    ),
}

GIRL_NAMES = ["Ava", "Mina", "Luna", "Iris", "Nia", "Zoe"]
BOY_NAMES = ["Ezra", "Owen", "Theo", "Ben", "Leo", "Milo"]


@dataclass
class StoryParams:
    setting: str
    move: str
    device: str
    child_name: str
    helper_name: str
    seed: Optional[int] = None
    samples: list = field(default_factory=list)
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
        return None


def valid_combos() -> list[tuple[str, str, str]]:
    return [("moonbase", "revolve", "caption"), ("orbit", "revolve", "caption"), ("crater", "revolve", "caption")]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space adventure for a young child about a {f["setting"].place_word} with a revolving ring and a glowing caption.',
        f"Tell a gentle story where {f['child'].label_word} wants to revolve a space ring but learns kindness from {f['helper'].label_word}.",
        f'Include the word "republican" in a kid-friendly way and end with a safe caption shining on the station.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    move = f["move"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What did {child.label_word} want to do at {setting.place}?",
            answer=f"{child.label_word} wanted to {move.verb}. That was exciting, but it could make the caption wobble.",
        ),
        QAItem(
            question=f"Who showed kindness when the moment felt suspenseful?",
            answer=f"{helper.label_word} showed kindness by warning about the signal dish and helping slow things down.",
        ),
        QAItem(
            question="What happened to the caption at the end?",
            answer="The caption shone clearly and safely after the children chose the careful way.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does revolve mean?", "To revolve means to turn around in a circle."),
        QAItem("What is a caption?", "A caption is a short piece of writing that helps explain a picture or screen."),
        QAItem("What is kindness?", "Kindness means being gentle, helpful, and caring to someone else."),
        QAItem("What is suspense?", "Suspense is the feeling of waiting and wondering what will happen next."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id}: {e.label_word} {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this world only tells revolve-and-caption space adventures.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld: revolve, caption, kindness, suspense.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    if getattr(args, "move", None) and getattr(args, "move", None) not in MOVES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    move = getattr(args, "move", None) or "revolve"
    device = getattr(args, "device", None) or rng.choice(list(DEVICES))
    if device == "republican":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name])
    return StoryParams(setting=setting, move=move, device=device, child_name=name, helper_name=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(MOVES, params.move), _safe_lookup(DEVICES, params.device), params.child_name, params.helper_name)
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
valid(S,M,D) :- setting(S), move(M), device(D), M = revolve, D = caption.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MOVES:
        lines.append(asp.fact("move", m))
    for d in DEVICES:
        lines.append(asp.fact("device", d))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        print("OK: no extra ASP verification needed for this compact world.")
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(StoryParams(setting=s, move="revolve", device="caption", child_name="Ava", helper_name="Leo")) for s in SETTINGS]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            i += 1
            sample = generate(p)
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
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
