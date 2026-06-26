#!/usr/bin/env python3
"""
storyworlds/worlds/sustain_duck_surprise_teamwork_conflict_superhero_story.py
=============================================================================

A small superhero story world with a duck, a surprise, teamwork, and conflict.

Seed tale used to build the world:
---
A little superhero named Nova wanted to help everyone in the city. One windy afternoon,
Nova and her sidekick Pip heard a surprised quack from the fountain square. A duck had
gotten stuck on a floating sign, and the sign was drifting toward a storm drain. Nova
wanted to swoop in alone, but the duck flapped wildly, Pip shouted advice, and Nova and
Pip briefly argued about the safest plan. Then they remembered they were a team. Nova
held the line, Pip brought a net, and together they guided the duck to shore. The duck
waddled away safely, and Nova learned that real hero work can be sustained by teamwork.

Core causal model:
---
    surprise event              -> actor.memes["surprise"] += 1
    conflict between heroes      -> actor.memes["conflict"] += 1
    teamwork plan succeeds       -> rescue progress increases
    rescue progress reaches 2    -> duck is sustained safely
    sustained duck               -> hero pride and relief increase
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
# Domain model
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
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    duck: object | None = None
    hero: object | None = None
    sidekick: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "shero"}
        male = {"boy", "man", "father", "hero"}
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
    place: str = "the fountain square"
    weather: str = "windy"
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
class Event:
    id: str
    kind: str
    verb: str
    sound: str
    risk: str
    keyword: str
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
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    prep: str
    tail: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.rescue_steps: int = 0
        self.duck_safe: bool = False

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "fountain": Setting(place="the fountain square", weather="windy"),
    "rooftop": Setting(place="the rooftop garden", weather="stormy"),
    "harbor": Setting(place="the harbor pier", weather="foggy"),
}

EVENTS = {
    "surprise_quack": Event(
        id="surprise_quack",
        kind="surprise",
        verb="hear a sudden quack",
        sound="quack",
        risk="the duck looked scared and the water was moving fast",
        keyword="surprise",
        tags={"surprise", "duck"},
    ),
    "storm_drain": Event(
        id="storm_drain",
        kind="conflict",
        verb="see the sign drift toward the storm drain",
        sound="whoosh",
        risk="the duck could slide into danger",
        keyword="conflict",
        tags={"conflict", "duck"},
    ),
}

TOOLS = {
    "net": Tool(
        id="net",
        label="a rescue net",
        phrase="a bright rescue net",
        helps={"duck"},
        prep="grab the rescue net",
        tail="held the net steady",
    ),
    "rope": Tool(
        id="rope",
        label="a rope line",
        phrase="a strong rope line",
        helps={"teamwork"},
        prep="tie a rope line to the railing",
        tail="kept the team anchored",
    ),
    "signal": Tool(
        id="signal",
        label="a signal mirror",
        phrase="a shiny signal mirror",
        helps={"surprise"},
        prep="flash a signal mirror",
        tail="sent a bright flash across the square",
    ),
}

HEROES = ["Nova", "Pip", "Sage", "Comet"]
TRAITS = ["brave", "kind", "quick-thinking", "calm"]


@dataclass
class StoryParams:
    place: str
    event: str
    tool: str
    hero: str
    sidekick: str
    trait: str
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
event_kind(E,K) :- event(E), kind(E,K).
tool_help(T,K) :- tool(T), helps(T,K).
valid_combo(P,E,T) :- setting(P), event(E), tool(T),
                      event_kind(E,K), tool_help(T,K).
#show valid_combo/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for eid, e in EVENTS.items():
        lines.append(asp.fact("event", eid))
        lines.append(asp.fact("kind", eid, e.kind))
        for tag in sorted(e.tags):
            lines.append(asp.fact("tag", eid, tag))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(t.helps):
            lines.append(asp.fact("helps", tid, h))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_combo")))


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place in SETTINGS:
        for event_id, ev in EVENTS.items():
            for tool_id, tool in TOOLS.items():
                if ev.kind in tool.helps:
                    out.append((place, event_id, tool_id))
    return out


def asp_verify() -> int:
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_story(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))

    hero = world.add(Entity(id=params.hero, kind="character", type="hero", meters={}, memes={}))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="hero", meters={}, memes={}))
    duck = world.add(Entity(
        id="duck",
        kind="thing",
        type="duck",
        label="duck",
        phrase="a startled duck",
        meters={"unsafe": 1.0, "safety": 0.0},
        memes={"fear": 1.0},
    ))
    event = _safe_lookup(EVENTS, params.event)
    tool = _safe_lookup(TOOLS, params.tool)

    world.facts.update(hero=hero, sidekick=sidekick, duck=duck, event=event, tool=tool)

    # Act 1
    world.say(
        f"{hero.id} was a {params.trait} superhero who loved helping people at {world.setting.place}."
    )
    world.say(
        f"{sidekick.id} was {hero.id}'s teammate, and together they were ready for any surprise."
    )
    world.say(
        f"On a {world.setting.weather} day, they were fixing up the square when they heard a loud {event.sound}."
    )
    world.para()

    # Act 2
    hero.memes["surprise"] = 1.0
    sidekick.memes["surprise"] = 1.0
    world.say(
        f"They turned and saw {duck.phrase} near the water edge."
    )
    world.say(
        f"The duck was in trouble because {event.risk}."
    )
    hero.memes["conflict"] += 1.0
    sidekick.memes["conflict"] += 1.0
    world.say(
        f"{hero.id} wanted to rush in alone, but {sidekick.id} stopped them and said the best rescue needed teamwork."
    )
    world.say(
        f"{hero.id} frowned for a moment, and the two friends had a quick conflict about what to do first."
    )
    world.para()

    # Act 3
    world.say(
        f"Then they remembered what real heroes do."
    )
    world.say(
        f"{tool.prep}, and {sidekick.id} {tool.tail} while {hero.id} reached for {duck.id} carefully."
    )
    world.rescue_steps += 1
    world.say(
        f"They moved together: one led, one steadied, and the duck stayed calm."
    )
    world.rescue_steps += 1
    if world.rescue_steps >= 2:
        world.duck_safe = True
        duck.meters["safety"] = 1.0
        duck.memes["fear"] = 0.0
    hero.memes["pride"] = 1.0
    hero.memes["relief"] = 1.0
    sidekick.memes["pride"] = 1.0
    sidekick.memes["relief"] = 1.0
    hero.memes["conflict"] = 0.0
    sidekick.memes["conflict"] = 0.0
    world.say(
        f"At last, they guided the duck to safety, and it waddled away with a happy little quack."
    )
    world.say(
        f"{hero.id} smiled, because the rescue was not just strong, it was sustained by teamwork."
    )

    world.facts["resolved"] = world.duck_safe
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    sidekick = _safe_fact(world, f, "sidekick")
    return [
        f"Write a superhero story for a young child about {hero.id}, {sidekick.id}, and a duck.",
        f"Tell a gentle rescue story with surprise, conflict, and teamwork at {world.setting.place}.",
        f"Write a short superhero tale where a duck is rescued and the heroes learn to work together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, sidekick, duck, event = f["hero"], f["sidekick"], f["duck"], f["event"]
    return [
        QAItem(
            question=f"Who were the two superheroes in the story?",
            answer=f"The two superheroes were {hero.id} and {sidekick.id}. They worked near {world.setting.place}.",
        ),
        QAItem(
            question=f"What made the heroes surprised at first?",
            answer=f"They were surprised by a sudden {event.sound} and then saw {duck.phrase} in danger.",
        ),
        QAItem(
            question=f"What problem was the duck facing?",
            answer=f"The duck was facing trouble because {event.risk}. The heroes had to rescue it carefully.",
        ),
        QAItem(
            question=f"Why did the heroes argue for a moment?",
            answer=f"They had a conflict because {hero.id} wanted to rush in alone, while {sidekick.id} wanted a safer teamwork plan.",
        ),
        QAItem(
            question=f"How did the heroes solve the problem?",
            answer=f"They solved it by using a rescue tool and working together, and that teamwork kept the duck safe.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "surprise": [
        (
            "What is a surprise?",
            "A surprise is something unexpected that suddenly happens and makes people stop and look.",
        )
    ],
    "duck": [
        (
            "What is a duck?",
            "A duck is a bird that often swims, waddles on land, and says quack.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people work together and help each other do something well.",
        )
    ],
    "conflict": [
        (
            "What is a conflict?",
            "A conflict is a problem or disagreement that can happen when people want different things.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["event"].tags)
    tags.add("duck")
    tags.add("teamwork")
    tags.add("conflict")
    out: list[QAItem] = []
    for tag in ["surprise", "duck", "teamwork", "conflict"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE[tag])
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with a duck, surprise, conflict, and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
    ap.add_argument("--trait", choices=["brave", "kind", "quick-thinking", "calm"])
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
    combos = valid_combos()
    if getattr(args, "event", None) and getattr(args, "tool", None):
        ev, tool = _safe_lookup(EVENTS, getattr(args, "event", None)), _safe_lookup(TOOLS, getattr(args, "tool", None))
        if ev.kind not in tool.helps:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "event", None) is None or c[1] == getattr(args, "event", None))
        and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, event, tool = rng.choice(list(combos))
    hero = getattr(args, "hero", None) or rng.choice(HEROES)
    sidekick_choices = [h for h in HEROES if h != hero]
    sidekick = getattr(args, "sidekick", None) or rng.choice(sidekick_choices)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, event=event, tool=tool, hero=hero, sidekick=sidekick, trait=trait)


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
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  rescue_steps={world.rescue_steps}")
    lines.append(f"  duck_safe={world.duck_safe}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_valid_stories() -> list[tuple]:
    return asp_valid_combos()


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, event, tool) combos:\n")
        for place, event, tool in combos:
            print(f"  {place:12} {event:14} {tool}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="fountain", event="surprise_quack", tool="net", hero="Nova", sidekick="Pip", trait="brave"),
            StoryParams(place="harbor", event="storm_drain", tool="rope", hero="Sage", sidekick="Comet", trait="calm"),
            StoryParams(place="rooftop", event="surprise_quack", tool="signal", hero="Nova", sidekick="Sage", trait="quick-thinking"),
        ]
        samples = [build_story(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = build_story(params)
            i += 1
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
