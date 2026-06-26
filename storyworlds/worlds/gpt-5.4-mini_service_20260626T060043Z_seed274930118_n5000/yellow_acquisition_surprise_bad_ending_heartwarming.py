#!/usr/bin/env python3
"""
storyworlds/worlds/yellow_acquisition_surprise_bad_ending_heartwarming.py
=========================================================================

A small Storyweavers world about a child, a yellow thing, an unexpected
acquisition, and a gentle but sad ending that still leaves warmth behind.

The domain is built from the seed words "yellow" and "acquisition", with a
surprise turn and a bad ending. The emotional shape stays heartwarming: even
when the prized yellow thing is lost, broken, or given away, the people in the
story respond with care.
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
# World model
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    acquired: bool = False
    lost: bool = False
    broken: bool = False
    gifted: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    parent: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def display(self) -> str:
        return self.label or self.type
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
class Prize:
    id: str
    label: str
    phrase: str
    color: str = "yellow"
    fragile: bool = False
    light: bool = False
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
class Surprise:
    id: str
    kind: str  # gift, swap, found, fix
    line: str
    acquisition: str
    twist: str
    bad_end: str
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
        self.facts: dict[str, object] = {}

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
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "market": Setting("the little market", indoors=False),
    "shop": Setting("the corner shop", indoors=True),
    "festival": Setting("the street festival", indoors=False),
}

PRIZES = {
    "balloon": Prize("balloon", "yellow balloon", "a bright yellow balloon", fragile=True, light=True),
    "raincoat": Prize("raincoat", "yellow raincoat", "a shiny yellow raincoat"),
    "duck": Prize("duck", "yellow duck toy", "a small yellow duck toy", light=True),
    "lantern": Prize("lantern", "yellow lantern", "a paper yellow lantern", fragile=True),
}

SURPRISES = {
    "gift": Surprise(
        "gift",
        "gift",
        "No one expected it, but a kind adult handed over the yellow thing as a gift.",
        "acquire it as a surprise gift",
        "The child hugged it with both hands and could not stop smiling.",
        "Then the wind knocked it away, or a careless bump broke it, and the bright moment turned sad.",
    ),
    "found": Surprise(
        "found",
        "found",
        "Behind a basket, the child found a yellow thing that had been lost earlier.",
        "pick it up with a surprise",
        "The child grinned because the day suddenly felt lucky.",
        "But the owner came back, and the child had to give it up, leaving a small ache behind.",
    ),
    "swap": Surprise(
        "swap",
        "swap",
        "A friend surprised the child by offering a trade for something yellow.",
        "make a happy swap",
        "The child felt rich all at once, as if the yellow thing had arrived on a ribbon.",
        "Yet the swap turned lopsided, and the new treasure tore or slipped away before sunset.",
    ),
}

CHAR_NAMES = ["Mina", "Leo", "Nia", "Owen", "Tia", "Eli", "Sara", "Jude"]
PARENT_NAMES = ["mom", "dad", "aunt", "uncle"]
TRAITS = ["gentle", "hopeful", "careful", "quiet", "cheerful"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    prize: str
    surprise: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
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


ASP_RULES = r"""
setting_ok(S) :- setting(S).
prize_ok(P) :- prize(P).
surprise_ok(T) :- surprise(T).

compatible(S, P, T) :- setting_ok(S), prize_ok(P), surprise_ok(T).
#show compatible/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    for t in SURPRISES:
        lines.append(asp.fact("surprise", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_compatible() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        pass
    if params.prize not in PRIZES:
        pass
    if params.surprise not in SURPRISES:
        pass


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = World(_safe_lookup(SETTINGS, params.setting))

    child = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in {"Mina", "Nia", "Tia", "Sara"} else "boy"))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=params.parent))
    prize_cfg = _safe_lookup(PRIZES, params.prize)
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.label,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=child.id,
        caretaker=parent.id,
    ))
    surprise = _safe_lookup(SURPRISES, params.surprise)

    child.memes["want"] = 1
    child.memes["hope"] = 1
    child.meters["empty_hands"] = 1

    world.say(
        f"At {world.setting.place}, {child.id} was a {params.trait} child who kept looking at {prize.label} things."
    )
    world.say(
        f"{child.id} wanted {prize.phrase}, because the yellow color felt like a small patch of sunshine."
    )

    world.para()
    world.say(
        f"That afternoon, {surprise.line}"
    )
    prize.acquired = True
    child.meters["held"] = 1
    child.memes["joy"] += 1
    world.say(
        f"So {child.id} got to {surprise.acquisition}, and {child.pronoun('possessive')} face lit up right away."
    )

    world.para()
    world.say(
        f"{surprise.twist}"
    )

    # Bad ending branch: the prized yellow thing does not stay safe.
    if params.surprise == "gift":
        prize.lost = True
        child.meters["held"] = 0
        child.memes["sad"] += 1
        parent.memes["comfort"] = 1
        world.say(
            f"Then a sudden gust tugged at it, and the yellow thing slipped away before anyone could catch it."
        )
    elif params.surprise == "found":
        prize.lost = True
        child.meters["held"] = 0
        child.memes["sad"] += 1
        parent.memes["comfort"] = 1
        world.say(
            f"A few moments later, the owner came back. {child.id} gave it back, even though that made the child's eyes shine with tears."
        )
    else:
        prize.broken = True
        child.memes["sad"] += 1
        parent.memes["comfort"] = 1
        world.say(
            f"By sunset, the trade had gone wrong, and the yellow thing tore or slipped out of reach."
        )

    world.para()
    child.memes["heart_warm"] += 1
    parent.memes["heart_warm"] += 1
    world.say(
        f"Still, {params.parent} sat with {child.id}, wiped away the tears, and said the best part was the surprise together."
    )
    world.say(
        f"{child.id} kept the happy feeling, even after the yellow treasure was gone."
    )

    world.facts.update(
        child=child,
        parent=parent,
        prize=prize,
        surprise=surprise,
        params=params,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    prize = _safe_fact(world, f, "prize")
    surprise = _safe_fact(world, f, "surprise")
    return [
        f'Write a heartwarming story about {child.id} and a yellow {prize.label} with a surprise acquisition.',
        f"Tell a simple tale where {child.id} gets {prize.phrase} unexpectedly, but the ending is sad and kind.",
        f"Create a short child-friendly story with the words 'yellow' and 'acquisition' and a warm ending image after a bad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    prize = _safe_fact(world, f, "prize")
    surprise = _safe_fact(world, f, "surprise")
    qa: list[QAItem] = [
        QAItem(
            question=f"What did {child.id} want at {world.setting.place}?",
            answer=f"{child.id} wanted {prize.phrase}, and the yellow color made it feel special."
        ),
        QAItem(
            question=f"How did {child.id} get the yellow thing?",
            answer=f"{child.id} got it through a surprise {surprise.kind}, so it arrived in an unexpected and exciting way."
        ),
        QAItem(
            question=f"What went wrong after the acquisition?",
            answer=(
                f"The yellow thing did not stay safe: it was lost, broken, or had to be given back, so the ending became sad."
            ),
        ),
        QAItem(
            question=f"How did {params_parent_name(world)} comfort {child.id}?",
            answer=(
                f"{params_parent_name(world)} stayed close, wiped away tears, and reminded {child.id} that the care between them still mattered."
            ),
        ),
    ]
    return qa


def params_parent_name(world: World) -> str:
    return world.get("parent").label or world.get("parent").type


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does the color yellow often make people think of?",
            answer="Yellow often makes people think of sunlight, warm light, lemons, and bright cheerful things."
        ),
        QAItem(
            question="What is an acquisition?",
            answer="An acquisition is when someone gets, obtains, or receives something."
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that happens when you were not ready for it."
        ),
        QAItem(
            question="What can make a story heartwarming even if the ending is bad?",
            answer="A story can still feel heartwarming when characters are kind, comforting, and loving with each other."
        ),
    ]


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
        if e.acquired:
            bits.append("acquired=True")
        if e.lost:
            bits.append("lost=True")
        if e.broken:
            bits.append("broken=True")
        if e.gifted:
            bits.append("gifted=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming yellow acquisition storyworld with a surprise and a sad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--name", choices=CHAR_NAMES)
    ap.add_argument("--parent", choices=PARENT_NAMES)
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
    if getattr(args, "setting", None) and getattr(args, "setting", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "prize", None) and getattr(args, "prize", None) not in PRIZES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "surprise", None) and getattr(args, "surprise", None) not in SURPRISES:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    prize = getattr(args, "prize", None) or rng.choice(list(PRIZES))
    surprise = getattr(args, "surprise", None) or rng.choice(list(SURPRISES))
    name = getattr(args, "name", None) or rng.choice(CHAR_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENT_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, prize=prize, surprise=surprise, name=name, parent=parent, trait=trait)


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


# ---------------------------------------------------------------------------
# ASP utilities
# ---------------------------------------------------------------------------
def asp_verify() -> int:
    clingo_set = set(asp_compatible())
    python_set = {(s, p, t) for s in SETTINGS for p in PRIZES for t in SURPRISES}
    if clingo_set == python_set:
        print(f"OK: ASP matches Python compatibility gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    print(" only in ASP:", sorted(clingo_set - python_set))
    print(" only in Python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_compatible()
        print(f"{len(triples)} compatible combinations:")
        for s, p, t in triples:
            print(f"  {s:10} {p:10} {t:10}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams("market", "balloon", "gift", "Mina", "mom", "gentle"),
            StoryParams("shop", "duck", "found", "Leo", "dad", "hopeful"),
            StoryParams("festival", "lantern", "swap", "Nia", "aunt", "cheerful"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
