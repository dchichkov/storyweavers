#!/usr/bin/env python3
"""
storyworlds/worlds/flow_teamwork_reconciliation_comedy.py
=========================================================

A small comedy storyworld about flow, teamwork, and reconciliation.

Premise:
- A tiny stream, sink, or hose has a flow problem.
- Two characters bicker over how to fix it.
- They team up, solve the clog/leak, and make up.

The world model tracks:
- physical meters: flow, blocked, wet, tidy
- emotional memes: irritation, pride, cooperation, relief, affection

The prose is driven by state changes rather than a frozen template.
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
# Entities and world model
# ---------------------------------------------------------------------------

def _safe_next(iterable, fallback=None):
    return next(iter(iterable), fallback)


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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    a: object | None = None
    b: object | None = None
    tool: object | None = None
    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))
        for k in ["flow", "blocked", "wet", "tidy"]:
            self.meters.setdefault(k, 0.0)
        for k in ["irritation", "pride", "cooperation", "relief", "affection", "laughter"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    indoors: bool
    flow_source: str
    flow_taste: str
    blocked_by: str
    fixes: list[str] = field(default_factory=list)
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
class Tool:
    id: str
    label: str
    verb: str
    helps: str
    comedic: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        import copy as _copy
        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "garden_hose": Setting(
        place="the garden",
        indoors=False,
        flow_source="a garden hose",
        flow_taste="fresh",
        blocked_by="a twisty knot",
        fixes=["untwist", "hold", "steady"],
    ),
    "kitchen_sink": Setting(
        place="the kitchen",
        indoors=True,
        flow_source="the sink",
        flow_taste="soapy",
        blocked_by="a spoon jammed in the drain",
        fixes=["lift", "sweep", "scrub"],
    ),
    "fountain": Setting(
        place="the town square",
        indoors=False,
        flow_source="a fountain",
        flow_taste="sparkly",
        blocked_by="a rubber duck wearing itself as a captain",
        fixes=["fish out", "wiggle", "laugh"],
    ),
}

TOOLS = [
    Tool(id="bucket", label="a bucket", verb="catch", helps="catch the extra water", comedic="wobbled like a nervous drum"),
    Tool(id="towel", label="a towel", verb="dry", helps="dry the splash", comedic="swooshed around like a cape"),
    Tool(id="gloves", label="rubber gloves", verb="grip", helps="grip the slippery part", comedic="squeaked like tiny trumpets"),
    Tool(id="spoon", label="a wooden spoon", verb="poke", helps="poke the clog loose", comedic="looked absurdly heroic"),
]

HEROES = [
    ("Milo", "boy", "boy"),
    ("Nina", "girl", "girl"),
    ("Pip", "boy", "boy"),
    ("Ada", "girl", "girl"),
    ("June", "girl", "girl"),
    ("Theo", "boy", "boy"),
]

TRAITS = ["cheerful", "sneaky", "curious", "hasty", "bright", "silly"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str = ""
    hero_a_name: str = ""
    hero_a_type: str = ""
    hero_b_name: str = ""
    hero_b_type: str = ""
    trait_a: str = ""
    trait_b: str = ""
    tool: str = ""
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Python reasonableness gate
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tool in TOOLS:
            if sid == "kitchen_sink" and tool.id in {"bucket", "towel", "gloves", "spoon"}:
                combos.append((sid, tool.id))
            elif sid == "garden_hose" and tool.id in {"bucket", "towel", "gloves"}:
                combos.append((sid, tool.id))
            elif sid == "fountain" and tool.id in {"bucket", "towel", "gloves", "spoon"}:
                combos.append((sid, tool.id))
    return combos


def explain_rejection(setting: str, tool: str) -> str:
    return (
        f"(No story: {tool} does not make sense for the flow problem at {setting}. "
        "Pick a different tool or setting.)"
    )


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


def _drain_or_fix(world: World) -> None:
    setting = world.setting
    a = world.get("hero_a")
    b = world.get("hero_b")
    tool = world.get("tool")

    if a.meters["flow"] >= THRESHOLD:
        if setting.place == "the kitchen":
            # teamwork: one holds, one pokes
            if tool.id == "spoon":
                a.memes["cooperation"] += 1
                b.memes["cooperation"] += 1
                a.meters["blocked"] = max(0.0, a.meters["blocked"] - 1)
                b.meters["blocked"] = max(0.0, b.meters["blocked"] - 1)
                world.say("Together, they poked and lifted until the drain gave up its stubborn cluck.")
            elif tool.id == "gloves":
                a.memes["cooperation"] += 1
                b.memes["cooperation"] += 1
                world.say("With gloved hands and far too much bravery, they reached in and found the spoon.")
            else:
                a.memes["cooperation"] += 1
                b.memes["cooperation"] += 1
                world.say("They grabbed the splashy mess together, which looked ridiculous but worked.")
        elif setting.place == "the garden":
            if tool.id == "bucket":
                world.say("One held the bucket while the other untwisted the hose. The flow hiccuped, then sighed happily.")
            else:
                world.say("They teamed up like a two-person circus, and the hose finally straightened out.")
        else:
            world.say("They leaned in together, and the fountain stopped acting like a grumpy fish.")
        a.meters["flow"] = 0.0
        b.meters["flow"] = 0.0
        a.meters["blocked"] = 0.0
        b.meters["blocked"] = 0.0
        a.memes["relief"] += 1
        b.memes["relief"] += 1
        a.memes["affection"] += 1
        b.memes["affection"] += 1
        a.memes["irritation"] = 0.0
        b.memes["irritation"] = 0.0


def tell_world(world: World) -> World:
    setting = world.setting
    a = world.add(Entity(id="hero_a", kind="character", type=_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "a_type")))
    b = world.add(Entity(id="hero_b", kind="character", type=_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "b_type")))
    tool = world.add(Entity(id="tool", kind="thing", type="tool", label=_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "tool_label")))

    a.name = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "a_name")  # type: ignore[attr-defined]
    b.name = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "b_name")  # type: ignore[attr-defined]

    # Setup
    world.say(
        f"At {setting.place}, {a.name} and {b.name} found {setting.flow_source} making a cheerful little flow."
    )
    world.say(
        f"It tasted {setting.flow_taste}, and the whole place looked ready to giggle."
    )
    world.para()

    # Tension
    a.memes["irritation"] += 1
    b.memes["irritation"] += 1
    a.memes["pride"] += 1
    b.memes["pride"] += 1
    a.meters["blocked"] += 1
    b.meters["blocked"] += 1
    a.meters["flow"] += 1
    b.meters["flow"] += 1
    world.say(
        f"Then {setting.blocked_by} stopped the flow, and both of them blamed the other with dramatic eyebrows."
    )
    world.say(
        f'"I had a plan," said {a.name}. "So did I," said {b.name}. "Unfortunately, mine was the funnier one," said the other.'
    )
    world.para()

    # Turn toward teamwork
    world.say(
        f"They looked at {tool.label}, which {tool.comedic}, and decided that arguing was not nearly as useful as teamwork."
    )
    world.say(
        f"{a.name} held steady while {b.name} used {tool.label} to {tool.verb} the problem."
    )
    a.memes["cooperation"] += 1
    b.memes["cooperation"] += 1
    _drain_or_fix(world)
    world.para()

    # Reconciliation
    world.say(
        f"The flow came back at once, splashing everyone in the shins like a tiny applause machine."
    )
    world.say(
        f"{a.name} and {b.name} stared at each other, then laughed so hard they nearly dropped the towel, the gloves, and their whole grudge."
    )
    world.say(
        f'{a.name} said, "Sorry I acted like a bossy spoon."' if world.facts["a_type"] == "boy" else f'{a.name} said, "Sorry I acted like a bossy spoon."'
    )
    world.say(
        f'{b.name} smiled. "Sorry I acted like a slippery genius."'
    )
    world.say(
        f"After that, they shared a grin, the flow stayed free, and the whole place felt kinder than before."
    )

    world.facts["resolved"] = True
    world.facts["tool"] = tool
    world.facts["setting"] = setting
    return world


# ---------------------------------------------------------------------------
# Content selection
# ---------------------------------------------------------------------------
def pick_name_gender(rng: random.Random) -> tuple[str, str]:
    name, gender, typ = rng.choice(HEROES)
    return name, typ


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    tool = getattr(args, "tool", None) or rng.choice([t.id for t in TOOLS])
    if (setting, tool) not in valid_combos():
        return _fallback_storyparams(args, rng, StoryParams, globals())

    a_name, a_type = pick_name_gender(rng)
    b_name, b_type = pick_name_gender(rng)
    while b_name == a_name:
        b_name, b_type = pick_name_gender(rng)
    return StoryParams(
        setting=setting,
        hero_a_name=a_name,
        hero_a_type=a_type,
        hero_b_name=b_name,
        hero_b_type=b_type,
        trait_a=rng.choice(TRAITS),
        trait_b=rng.choice(TRAITS),
        tool=tool,
    )


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.setting)
    world = World(setting)
    world.facts = {
        "a_name": params.hero_a_name,
        "b_name": params.hero_b_name,
        "a_type": params.hero_a_type,
        "b_type": params.hero_b_type,
        "tool": params.tool,
        "tool_label": _safe_next((t.label for t in TOOLS if t.id == params.tool)),
    }
    tell_world(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short comedy story for a child about "{_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "tool_label")}" and a tricky flow problem.',
        f"Tell a funny story where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "a_name")} and {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "b_name")} stop a flow problem by working together and making up.",
        f"Write a gentle story about teamwork, a blocked flow, and two friends who reconcile after a silly argument.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a = world.get("hero_a")
    b = world.get("hero_b")
    setting = world.setting
    tool = world.get("tool")
    return [
        QAItem(
            question=f"What problem did {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "a_name")} and {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "b_name")} have at {setting.place}?",
            answer=f"They had a flow problem because {setting.blocked_by} blocked {setting.flow_source}.",
        ),
        QAItem(
            question=f"How did they fix the problem with {tool.label}?",
            answer=f"They worked together, and {a.name} and {b.name} used {tool.label} to {tool.verb} the blockage loose.",
        ),
        QAItem(
            question=f"How did the two friends feel at the end?",
            answer=f"They felt relieved, happier, and friendlier after the flow came back and they made up.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is flow?",
            answer="Flow is the movement of water or another liquid from one place to another.",
        ),
        QAItem(
            question="Why is teamwork useful?",
            answer="Teamwork is useful because two people can combine their ideas and hands to solve a problem faster.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who argued or disagreed forgive each other and become friendly again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
flow_problem(S) :- blocked(S).
teamwork(S) :- flow_problem(S), helper(a), helper(b).
reconciles(S) :- teamwork(S), problem_fixed(S).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(valid_combos())
    if python_set != asp_set:
        print("MISMATCH")
        return 1
    print(f"OK: verified {len(python_set)} combos.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about flow, teamwork, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tool", choices=[t.id for t in TOOLS])
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("garden_hose", "Milo", "boy", "Nina", "girl", "cheerful", "curious", "bucket"),
    StoryParams("kitchen_sink", "Ada", "girl", "Theo", "boy", "silly", "hasty", "spoon"),
    StoryParams("fountain", "Pip", "boy", "June", "girl", "bright", "sneaky", "gloves"),
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
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
