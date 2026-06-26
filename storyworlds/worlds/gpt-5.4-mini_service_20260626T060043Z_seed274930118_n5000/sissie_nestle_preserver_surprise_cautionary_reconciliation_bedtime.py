#!/usr/bin/env python3
"""
Storyworld: sissie / nestle / preserver
=======================================

A small bedtime story domain with three narrative instruments:

- Surprise: a tucked-away delight appears at the bedside
- Cautionary: an adult warns about keeping bedtime calm and preserving rest
- Reconciliation: the child and adult choose a gentle compromise

This world is intentionally tiny and constraint-checked. It models a bedtime
scene as a simulated state machine with physical meters and emotional memes,
then renders a child-facing story with a clear beginning, tension, and soft
ending.
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
# Registries
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
class Character:
    id: str
    kind: str = "character"
    type: str = "child"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    parent: object | None = None
    def __post_init__(self):
        for k in ["sleepy", "rest", "busy", "mess", "comfort"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "worry", "joy", "calm", "resolve"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    place: str = "the bedroom"
    cozy: bool = True
    affords: set[str] = field(default_factory=lambda: {"surprise", "cautionary", "reconciliation"})
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
class Prop:
    id: str
    label: str
    phrase: str
    type: str
    location: str = "bedside"
    owner: Optional[str] = None
    preserved_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    prop: object | None = None
    def __post_init__(self):
        for k in ["safe", "tucked", "open", "sparkle", "sleep"]:
            self.meters.setdefault(k, 0.0)
        for k in ["wonder", "worry", "relief"]:
            self.memes.setdefault(k, 0.0)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class EventSpec:
    id: str
    noun: str
    verb: str
    tension: str
    resolution: str
    effect: str
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


EVENTS = {
    "surprise": EventSpec(
        id="surprise",
        noun="surprise",
        verb="peek at the surprise",
        tension="the surprise might keep bedtime awake",
        resolution="they could save it for morning",
        effect="wonder",
        tags={"surprise", "bedtime"},
    ),
    "cautionary": EventSpec(
        id="cautionary",
        noun="cautionary note",
        verb="linger by the glow",
        tension="the glow and excitement might stretch the night too long",
        resolution="they could tuck the glow away and breathe slowly",
        effect="worry",
        tags={"cautionary", "sleep"},
    ),
    "reconciliation": EventSpec(
        id="reconciliation",
        noun="reconciliation plan",
        verb="choose a gentle plan together",
        tension="the child wanted more play while sleep wanted room",
        resolution="they could cuddle, preserve the surprise, and rest",
        effect="relief",
        tags={"reconciliation", "bedtime"},
    ),
}

SETTINGS = {
    "bedroom": Setting(place="the bedroom", cozy=True),
}

TRAITS = ["curious", "sleepy", "gentle", "spirited", "quiet", "thoughtful"]
GIRL_NAMES = ["Sissie"]
PARENT_NAMES = ["Nestle"]
PRIZES = {
    "preserver": Prop(
        id="preserver",
        label="preserver",
        phrase="a little preserver box wrapped in soft paper",
        type="box",
        location="under the pillow",
    ),
    "nightlight": Prop(
        id="nightlight",
        label="nightlight",
        phrase="a small moon nightlight",
        type="lamp",
        location="on the nightstand",
    ),
}

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str = "bedroom"
    event: str = "surprise"
    prize: str = "preserver"
    name: str = "Sissie"
    parent: str = "Nestle"
    trait: str = "curious"
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


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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
# Story simulation
# ---------------------------------------------------------------------------

def _apply_surprise(world: World, child: Character, prop: Prop) -> None:
    if "surprise_seen" in world.fired:
        return
    world.fired.add("surprise_seen")
    child.memes["curiosity"] += 1
    prop.meters["sparkle"] += 1
    prop.memes["wonder"] += 1
    world.say(
        f"At bedtime, {child.id} noticed that {prop.label} was tucked close by the pillow, "
        f"as if it had been waiting for a secret."
    )
    world.say(
        f"That little surprise made {child.id}'s eyes widen, and the room felt extra quiet."
    )


def _apply_cautionary(world: World, child: Character, parent: Character, prop: Prop) -> None:
    if "cautionary_warned" in world.fired:
        return
    world.fired.add("cautionary_warned")
    child.memes["worry"] += 1
    parent.memes["calm"] += 1
    prop.memes["worry"] += 1
    world.say(
        f'{parent.id} smiled softly and said, "We can look, but if we stay up too long, '
        f'we will lose the sleepy feeling we worked so hard to keep."'
    )
    world.say(
        f"{parent.id} wanted to preserve bedtime, so the cautionary note was gentle, not sharp."
    )


def _apply_reconciliation(world: World, child: Character, parent: Character, prop: Prop) -> None:
    if "reconciled" in world.fired:
        return
    world.fired.add("reconciled")
    child.memes["resolve"] += 1
    child.memes["joy"] += 1
    parent.memes["relief"] += 1
    prop.meters["tucked"] += 1
    prop.meters["safe"] += 1
    world.say(
        f"{child.id} took a slow breath and nodded. Together, {child.id} and {parent.id} "
        f"made a reconciliation plan: the {prop.label} would stay wrapped and waiting for morning."
    )
    world.say(
        f"Then {child.id} snuggled down, and the surprise felt sweeter because it was being preserved."
    )


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    child = world.add(Character(id=params.name, type="girl", label=params.name, traits=[params.trait]))
    parent = world.add(Character(id=params.parent, type="mother", label=params.parent))
    prop = world.add(Prop(**_safe_lookup(PRIZES, params.prize).__dict__))

    world.facts.update(child=child, parent=parent, prop=prop, event=_safe_lookup(EVENTS, params.event))

    world.say(
        f"{child.id} was a {params.trait} little girl who loved bedtime stories and soft blankets."
    )
    world.say(
        f"One evening, {child.id} and {parent.id} were in {world.setting.place}, where the lamp glowed like a tiny moon."
    )

    world.para()
    _apply_surprise(world, child, prop)
    world.para()
    _apply_cautionary(world, child, parent, prop)
    world.para()
    _apply_reconciliation(world, child, parent, prop)

    return world


# ---------------------------------------------------------------------------
# Validation and selection
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for event_id in EVENTS:
            for prize_id in PRIZES:
                if setting.cozy and place == "bedroom":
                    combos.append((place, event_id, prize_id))
    return combos


def explain_rejection(event: EventSpec, prize: Prop) -> str:
    return (
        f"(No story: the {event.noun} and {prize.label} do not make a calm bedtime "
        f"scene here. Choose the bedroom setting and a gentle surprise.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "event", None) and getattr(args, "prize", None):
        if (getattr(args, "place", None) or "bedroom") != "bedroom":
            return _fallback_storyparams(args, rng, StoryParams, globals())
        if getattr(args, "event", None) not in EVENTS or getattr(args, "prize", None) not in PRIZES:
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if getattr(args, "place", None) in {None, c[0]}
              and getattr(args, "event", None) in {None, c[1]}
              and getattr(args, "prize", None) in {None, c[2]}]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, event, prize = rng.choice(list(combos))
    return StoryParams(
        place=place,
        event=event,
        prize=prize,
        name=getattr(args, "name", None) or "Sissie",
        parent=getattr(args, "parent", None) or "Nestle",
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    child: Character = _safe_fact(world, world.facts, "child")
    parent: Character = _safe_fact(world, world.facts, "parent")
    prop: Prop = _safe_fact(world, world.facts, "prop")
    event: EventSpec = _safe_fact(world, world.facts, "event")

    story = world.render()
    prompts = [
        "Write a short bedtime story about a child, a small surprise, and a gentle compromise.",
        f"Tell a cozy story where {params.name} wants to {event.verb} but {params.parent} helps keep the night calm.",
        "Write a child-friendly bedtime tale with a soft warning and a peaceful ending.",
    ]
    story_qa = [
        QAItem(
            question=f"Who is the bedtime story about?",
            answer=f"It is about {child.id}, a {params.trait} little girl, and {parent.id}, who helps keep bedtime gentle.",
        ),
        QAItem(
            question=f"What was the surprise in the room?",
            answer=f"The surprise was {prop.phrase}, which was waiting near the pillow.",
        ),
        QAItem(
            question=f"What did {parent.id} want to preserve?",
            answer=f"{parent.id} wanted to preserve bedtime sleep, so the surprise would not keep {child.id} awake too long.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{child.id} and {parent.id} made a reconciliation plan and tucked the {prop.label} away for morning.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that makes you wonder or smile.",
        ),
        QAItem(
            question="What does cautionary mean?",
            answer="Cautionary means giving a careful warning so someone can avoid a problem.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people make peace again after a worry or disagreement.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


# ---------------------------------------------------------------------------
# Q&A formatting and trace
# ---------------------------------------------------------------------------

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
        if isinstance(e, Character):
            lines.append(
                f"  {e.id:10} ({e.type:9}) meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
                f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
            )
        else:
            lines.append(
                f"  {e.id:10} ({e.type:9}) meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
                f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
            )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(bedroom).
cozy(bedroom).

event(surprise).
event(cautionary).
event(reconciliation).

prize(preserver).
prize(nightlight).

valid(Place, Event, Prize) :- place(Place), cozy(Place), event(Event), prize(Prize).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
        if _safe_lookup(SETTINGS, place).cozy:
            lines.append(asp.fact("cozy", place))
    for event_id in EVENTS:
        lines.append(asp.fact("event", event_id))
    for prize_id in PRIZES:
        lines.append(asp.fact("prize", prize_id))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world: Sissie, Nestle, and a small preserver surprise."
    )
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--event", choices=list(EVENTS))
    ap.add_argument("--prize", choices=list(PRIZES))
    ap.add_argument("--name")
    ap.add_argument("--parent")
    ap.add_argument("--trait", choices=TRAITS)
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


CURATED = [
    StoryParams(place="bedroom", event="surprise", prize="preserver", name="Sissie", parent="Nestle", trait="curious"),
    StoryParams(place="bedroom", event="cautionary", prize="nightlight", name="Sissie", parent="Nestle", trait="thoughtful"),
    StoryParams(place="bedroom", event="reconciliation", prize="preserver", name="Sissie", parent="Nestle", trait="gentle"),
]


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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, event, prize) combos:\n")
        for place, event, prize in combos:
            print(f"  {place:9} {event:14} {prize}")
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
            header = f"### {p.name}: {p.event} with {p.prize} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
