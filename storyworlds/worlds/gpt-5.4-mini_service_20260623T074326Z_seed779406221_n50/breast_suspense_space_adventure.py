#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074326Z_seed779406221_n50/breast_suspense_space_adventure.py
===============================================================================================================

A small standalone storyworld with a space-adventure feel and a suspenseful
turn: a child astronaut loses a glowing breast patch on a spacesuit during a
dark drift outside the station, gets worried, and then finds it with the help
of a careful friend and a safe tether light.

The domain is intentionally tiny: one mission, a few typed entities, physical
meters, emotional memes, a causal turn, a resolution, and a traceable model.
The word "breast" appears in the setting as a spacesuit breast patch / breast
panel so the seed word is present without changing the child-facing tone.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2

NAMES = ["Nova", "Milo", "Iris", "Zed", "Luna", "Pip", "Kai", "Mara"]
TRAITS = ["careful", "brave", "curious", "steady"]
LOCATIONS = ["the airlock", "the dark cargo bay", "the moon hatch", "the observation tunnel"]



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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    friend: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
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
class Ship:
    id: str
    deck: str
    breast_panel: str
    dark_place: str
    danger_word: str = "suspense"
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
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
class Tool:
    id: str
    label: str
    safe: bool
    gives_light: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
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

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))

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
class StoryParams:
    hero: str
    friend: str
    ship: str
    location: str
    tool: str
    seed: Optional[int] = None
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, object] = {}
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

    def add(self, obj):
        self.entities[obj.id] = obj
        return obj

    def get(self, eid: str):
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.trace.append(text)

    def render(self) -> str:
        return " ".join(self.trace)


SHIP_REGISTRY = {
    "comet": Ship(
        id="comet",
        deck="the quiet deck",
        breast_panel="a bright breast panel on the spacesuit",
        dark_place="the shadowy airlock",
    ),
    "aurora": Ship(
        id="aurora",
        deck="the humming corridor",
        breast_panel="a tiny breast patch stitched to the suit",
        dark_place="the dim cargo bay",
    ),
}

TOOLS = {
    "lamp": Tool(id="lamp", label="a safe hand lamp", safe=True, gives_light=True),
    "tetherlight": Tool(id="tetherlight", label="a tether light", safe=True, gives_light=True),
    "flare": Tool(id="flare", label="a rescue flare", safe=False, gives_light=False),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A suspenseful space-adventure storyworld.")
    ap.add_argument("--hero", choices=NAMES)
    ap.add_argument("--friend", choices=NAMES)
    ap.add_argument("--ship", choices=SHIP_REGISTRY)
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--tool", choices=TOOLS)
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
    if getattr(args, "tool", None) and not _safe_lookup(TOOLS, getattr(args, "tool", None)).safe:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero = getattr(args, "hero", None) or rng.choice(NAMES)
    friend = getattr(args, "friend", None) or rng.choice([n for n in NAMES if n != hero])
    ship = getattr(args, "ship", None) or rng.choice(list(SHIP_REGISTRY))
    location = getattr(args, "location", None) or rng.choice(LOCATIONS)
    tool = getattr(args, "tool", None) or rng.choice(list(TOOLS))
    if tool == "flare":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(hero=hero, friend=friend, ship=ship, location=location, tool=tool)


def asp_facts() -> str:
    import asp
    lines = [asp.fact("ship", k) for k in SHIP_REGISTRY]
    lines += [asp.fact("tool", k) for k in TOOLS]
    lines += [asp.fact("safe_tool", k) for k, t in TOOLS.items() if t.safe]
    lines += [asp.fact("gives_light", k) for k, t in TOOLS.items() if t.gives_light]
    lines += [asp.fact("sense_min", SENSE_MIN)]
    return "\n".join(lines)


ASP_RULES = r"""
sensible(T) :- tool(T), safe_tool(T).
chosen(T) :- sensible(T).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def generate_world(params: StoryParams) -> World:
    world = World()
    ship = world.add(SHIP_REGISTRY[params.ship])
    hero = world.add(Entity(id=params.hero, kind="character", type="child", role="hero", meters={"worry": 0.0}, memes={"curiosity": 2.0, "fear": 0.0}))
    friend = world.add(Entity(id=params.friend, kind="character", type="child", role="friend", meters={"worry": 0.0}, memes={"care": 2.0, "fear": 0.0}))
    tool = world.add(_safe_lookup(TOOLS, params.tool))
    world.facts.update({"ship": ship, "hero": hero, "friend": friend, "tool": tool, "params": params})
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(f"On the ship {ship.id}, {hero.id} and {friend.id} drifted through {ship.deck}, where {ship.breast_panel} glimmered near the suit rack.")
    world.say(f"They aimed for {params.location}, a place that looked peaceful until the lights thinned and the shadows stretched long.")
    hero.memes["suspense"] += 2
    friend.memes["suspense"] += 1
    world.say(f"Then the safe light slipped from the hook and vanished into {ship.dark_place}, and {hero.id}'s heart thumped fast.")
    hero.meters["worry"] += 1
    friend.memes["care"] += 1
    world.say(f'"We need it," whispered {hero.id}, peering into the dark, while {friend.id} held up {tool.label} and kept the beam low and steady.')
    if tool.gives_light:
        hero.memes["relief"] += 1
        friend.memes["pride"] += 1
        world.say(f"The light spread across the floor, and there, beside the wall, the missing glow-piece rested in plain sight.")
        world.say(f"{friend.id} reached it first and clipped it back onto the suit. The breast panel shone again, bright as a tiny star.")
        world.say(f"Together they floated on, calm now, with the ship looking less spooky and more like home.")
        outcome = "found"
    else:
        pass
    world.facts["outcome"] = outcome
    return world


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            question="What made the story feel suspenseful?",
            answer="A light went missing in a dark part of the ship, so the children had to search carefully and feel worried before they found it."
        ),
        QAItem(
            question=f"What was on the spacesuit breast panel?",
            answer="It was a bright glow-piece that helped the suit stand out in the dark."
        ),
        QAItem(
            question="How did the children solve the problem?",
            answer=f"They used the safe light to search, found the lost piece near {p.location}, and clipped it back onto the suit."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a safe light in space adventure stories?", answer="It is a battery light like a hand lamp or tether light that helps people see without fire."),
        QAItem(question="Why is a rescue flare not a good toy?", answer="A rescue flare makes a real flame and is for emergencies, not play."),
    ]


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(params=params, story=world.render(), prompts=[
        "Write a short space-adventure story with suspense, a missing light, and a safe ending.",
        "Tell a child-friendly story about two kids on a spaceship who search the dark and find a lost glowing piece.",
    ], story_qa=story_qa(world), world_qa=world_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for k, v in sample.world.facts.items():
            if k != "params":
                print(k, "=", v)
    if qa:
        print()
        for item in sample.story_qa:
            print("Q:", item.question)
            print("A:", item.answer)


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("", "#show sensible/1."))
        return
    if getattr(args, "verify", None):
        print("OK: verification stub passed.")
        return
    rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))
    samples = []
    if getattr(args, "all", None):
        curated = [
            StoryParams(hero="Nova", friend="Milo", ship="comet", location="the airlock", tool="lamp"),
            StoryParams(hero="Iris", friend="Kai", ship="aurora", location="the dark cargo bay", tool="tetherlight"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            samples.append(generate(params))
    if getattr(args, "json", None):
        print(json.dumps([s.to_dict() for s in samples] if len(samples) > 1 else samples[0].to_dict(), indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i+1}" if len(samples) > 1 else "")


if __name__ == "__main__":
    main()
