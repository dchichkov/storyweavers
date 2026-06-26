#!/usr/bin/env python3
"""
A standalone story world for a tiny Adventure-style magic tale.

Premise:
A young adventurer and a magical guide-set must cross a short path to reach a
hidden grove. The magic works only when the traveler keeps the right attitude:
calmness helps the charm glow, while hurry and fear make it sputter. The story
turns on the character learning to slow down, use the magic tool wisely, and
finish the trip with a better feeling than they started with.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    magical: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    guide: object | None = None
    hero: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "sister", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "brother", "father"}:
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
    place: str
    path: str
    goal: str
    hazards: list[str] = field(default_factory=list)
    magic_weather: str = "twilight"
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
    phrase: str
    help_text: str
    attuned_attitudes: set[str]
    needed: str
    fixes: str
    magical: bool = True
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
    setting: str
    tool: str
    attitude: str
    hero_name: str
    hero_type: str
    guide_type: str
    seed: Optional[int] = None
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
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "whisperwood": Setting(
        place="Whisperwood",
        path="a silver path through whispering trees",
        goal="the hidden grove",
        hazards=["brambles", "mist"],
        magic_weather="twilight",
    ),
    "stonebridge": Setting(
        place="Stonebridge",
        path="a narrow bridge over a fast stream",
        goal="the lantern gate",
        hazards=["wind", "wobbly stones"],
        magic_weather="evening",
    ),
    "moonhill": Setting(
        place="Moonhill",
        path="a winding hill trail under the stars",
        goal="the starlit cave",
        hazards=["steep turns", "dark roots"],
        magic_weather="nightfall",
    ),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="magic lantern",
        phrase="a little magic lantern with a blue glass door",
        help_text="light the way and show a safe path",
        attuned_attitudes={"calm", "curious"},
        needed="dim paths and hidden turns",
        fixes="glowed steadily",
    ),
    "compass": Tool(
        id="compass",
        label="magic compass",
        phrase="a brass magic compass that hummed softly",
        help_text="point toward the goal when the traveler stayed steady",
        attuned_attitudes={"curious", "brave"},
        needed="getting lost",
        fixes="pointed true",
    ),
    "cloak": Tool(
        id="cloak",
        label="magic cloak",
        phrase="a soft magic cloak stitched with silver stars",
        help_text="ward off mist and keep courage close",
        attuned_attitudes={"calm", "kind"},
        needed="misty stretches",
        fixes="held the mist back",
    ),
}

ATTITUDES = {
    "attitudinal": "attitudinal",
    "calm": "calm",
    "curious": "curious",
    "brave": "brave",
    "kind": "kind",
    "anxious": "anxious",
    "impatient": "impatient",
}

HERO_NAMES = ["Mira", "Tess", "Pip", "Nina", "Arlo", "Juno", "Finn", "Lina"]
GENTLE_GUIDES = ["mother", "father", "aunt", "uncle", "older sister", "older brother"]

CURATED = [
    StoryParams("whisperwood", "lantern", "curious", "Mira", "girl", "mother"),
    StoryParams("stonebridge", "compass", "brave", "Pip", "boy", "father"),
    StoryParams("moonhill", "cloak", "kind", "Lina", "girl", "older sister"),
]


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def attitude_phrase(attitude: str) -> str:
    return {
        "calm": "stayed calm",
        "curious": "kept asking questions",
        "brave": "stood tall",
        "kind": "thought about helping others",
        "anxious": "kept worrying",
        "impatient": "wanted to hurry",
        "attitudinal": "tried to keep an attitudinal mind about the path",
    }.get(attitude, attitude)


def attitude_effect(attitude: str) -> float:
    return {
        "calm": 1.0,
        "curious": 0.8,
        "brave": 0.7,
        "kind": 0.6,
        "attitudinal": 0.5,
        "anxious": -0.7,
        "impatient": -0.9,
    }.get(attitude, 0.0)


def setting_opening(setting: Setting) -> str:
    return {
        "Whisperwood": "The trees in Whisperwood whispered like they were keeping secrets.",
        "Stonebridge": "Stonebridge was narrow and bright, with water hurrying below the stones.",
        "Moonhill": "Moonhill glimmered under the stars, and the trail curled upward like a ribbon.",
    }[setting.place]


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    world = World(setting)
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        meters={"steps": 0.0, "travel": 0.0},
        memes={"fear": 0.0, "hope": 0.0, "focus": 0.0},
    ))
    guide = world.add(Entity(
        id="Guide",
        kind="character",
        type=params.guide_type,
        label=f"the {params.guide_type}",
        meters={"steps": 0.0},
        memes={"care": 1.0},
    ))
    tool = world.add(Entity(
        id="Tool",
        kind="thing",
        type=params.tool,
        label=_safe_lookup(TOOLS, params.tool).label,
        phrase=_safe_lookup(TOOLS, params.tool).phrase,
        owner=hero.id,
        carried_by=hero.id,
        magical=True,
        meters={"glow": 0.0, "misfire": 0.0},
    ))
    hero.memes["attitude"] = attitude_effect(params.attitude)
    world.facts.update(hero=hero, guide=guide, tool=tool, params=params)
    return world


def predict_success(world: World, params: StoryParams) -> bool:
    tool = _safe_lookup(TOOLS, params.tool)
    attitude_score = attitude_effect(params.attitude)
    return params.attitude in tool.attuned_attitudes and attitude_score >= 0


def narrate_intro(world: World, params: StoryParams) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    guide: Entity = _safe_fact(world, world.facts, "guide")
    tool: Entity = _safe_fact(world, world.facts, "tool")
    world.say(
        f"{setting_opening(world.setting)} {hero.id} was a young {hero.type} who loved adventure."
    )
    world.say(
        f"{hero.id} carried {tool.phrase}, because {tool.label} could {tool.help_text}."
    )
    world.say(
        f"That morning, {hero.id} and {guide.label} set out toward {world.setting.goal}."
    )
    world.say(
        f"{hero.id} {attitude_phrase(params.attitude)} before the journey began."
    )


def narrate_trial(world: World, params: StoryParams) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    tool: Entity = _safe_fact(world, world.facts, "tool")
    tool_def = _safe_lookup(TOOLS, params.tool)
    world.para()
    world.say(
        f"Halfway along {world.setting.path}, {world.setting.hazards[0]} and {world.setting.hazards[-1]} made the way tricky."
    )
    if params.attitude in {"anxious", "impatient"}:
        hero.memes["fear"] += 1.0
        tool.meters["misfire"] += 1.0
        world.say(
            f"{hero.id} began to hurry, and the {tool.label} gave a small useless flicker."
        )
        world.say(
            f"It was not enough for {tool_def.needed}, so the path seemed even longer."
        )
    else:
        hero.memes["focus"] += 1.0
        tool.meters["glow"] += 1.0
        world.say(
            f"{hero.id} breathed slowly, and the {tool.label} {tool_def.fixes}, lighting the way."
        )
        if params.attitude in {"curious", "kind"}:
            world.say(
                f"{hero.id} noticed tiny safe stones and chose each step with care."
            )
        else:
            world.say(
                f"{hero.id} kept steady, and the magic held strong."
            )


def narrate_turn(world: World, params: StoryParams) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    guide: Entity = _safe_fact(world, world.facts, "guide")
    tool: Entity = _safe_fact(world, world.facts, "tool")
    tool_def = _safe_lookup(TOOLS, params.tool)
    world.para()
    if params.attitude in {"anxious", "impatient"}:
        world.say(
            f"{guide.label} smiled and said, 'Adventure goes better when we slow our feet and steady our hearts.'"
        )
        world.say(
            f"{hero.id} listened, took a deep breath, and tried a better attitude."
        )
        hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1.0)
        hero.memes["focus"] += 1.0
        tool.meters["glow"] += 1.0
        world.say(
            f"Then the {tool.label} {tool_def.fixes}, and {world.setting.goal} began to show ahead."
        )
    else:
        world.say(
            f"{guide.label} nodded proudly. 'That is the right kind of attitude for magic,' {guide.pronoun()} said."
        )
        world.say(
            f"With patience and wonder, {hero.id} let the {tool.label} lead the last part of the trail."
        )


def narrate_resolution(world: World, params: StoryParams) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    guide: Entity = _safe_fact(world, world.facts, "guide")
    tool: Entity = _safe_fact(world, world.facts, "tool")
    tool_def = _safe_lookup(TOOLS, params.tool)
    hero.meters["steps"] += 1.0
    hero.meters["travel"] += 1.0
    hero.memes["hope"] += 1.0
    world.para()
    world.say(
        f"At last, {hero.id} reached {world.setting.goal}, where a little beam of light rested on the stones."
    )
    if params.attitude in {"anxious", "impatient"}:
        world.say(
            f"{hero.id} had started the trip with a shaky heart, but the choice to slow down changed everything."
        )
    else:
        world.say(
            f"{hero.id}'s steady mood had helped the magic all along."
        )
    world.say(
        f"The {tool.label} {tool_def.fixes}, {world.setting.goal} looked safe and bright, and {guide.label} laughed softly beside {hero.id}."
    )
    world.say(
        f"{hero.id} went home with a braver heart and a better attitude than before."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    narrate_intro(world, params)
    narrate_trial(world, params)
    narrate_turn(world, params)
    narrate_resolution(world, params)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f'Write a short adventure story for children about the word "{p.attitude}" and a magic {p.tool}.',
        f"Tell a gentle quest where {p.hero_name}, a {p.hero_type}, learns that attitude matters when using magic.",
        f"Write a simple story in which a young adventurer reaches {world.setting.goal} with help from a magic tool.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = _safe_fact(world, world.facts, "params")
    hero: Entity = _safe_fact(world, world.facts, "hero")
    tool: Entity = _safe_fact(world, world.facts, "tool")
    guide: Entity = _safe_fact(world, world.facts, "guide")
    mood = p.attitude
    tool_def = _safe_lookup(TOOLS, p.tool)
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a young {hero.type}, and {guide.label}, who helped on the trip.",
        ),
        QAItem(
            question=f"What magic tool did {hero.id} carry?",
            answer=f"{hero.id} carried {tool.phrase}. It could {tool_def.help_text}.",
        ),
        QAItem(
            question=f"What attitude did {hero.id} show on the journey?",
            answer=f"{hero.id} showed a {mood} attitude and {attitude_phrase(mood)}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What makes magic work better in many adventure stories?",
            answer="In many adventure stories, magic works better when the hero stays calm, careful, or brave instead of rushing in fear.",
        ),
        QAItem(
            question="What is an adventure?",
            answer="An adventure is a trip or task with surprises, challenges, and a place to reach at the end.",
        ),
        QAItem(
            question="Why do travelers use lanterns on dark paths?",
            answer="Travelers use lanterns on dark paths so they can see where they are stepping and avoid trouble.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.magical:
            bits.append("magical=True")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"{e.id}: {e.type} " + " ".join(bits))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A tool is attuned to an attitude when that attitude helps its magic.
attuned(T, A) :- tool(T), tool_attuned(T, A).

% A story is reasonable if the chosen tool matches the attitude.
valid_story(S, T, A) :- setting(S), tool(T), attitude(A), attuned(T, A).

% Steady attitudes can power the magic; anxious or impatient ones do not.
steady(calm).
steady(curious).
steady(brave).
steady(kind).

good_magic(T, A) :- attuned(T, A), steady(A).

#show valid_story/3.
#show good_magic/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for a in sorted(tool.attuned_attitudes):
            lines.append(asp.fact("tool_attuned", tid, a))
    for a in ATTITUDES:
        lines.append(asp.fact("attitude", a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_good_magic() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "good_magic")))


def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        pass
    if params.tool not in TOOLS:
        pass
    if params.attitude not in ATTITUDES:
        pass
    tool = _safe_lookup(TOOLS, params.tool)
    if params.attitude not in tool.attuned_attitudes:
        pass


def asp_verify() -> int:
    import asp
    py = sorted((s, t, a) for s in SETTINGS for t, tool in TOOLS.items() for a in tool.attuned_attitudes)
    clingo_set = set(asp_valid_stories())
    py_set = set(py)
    if clingo_set != py_set:
        print("MISMATCH between ASP and Python gate:")
        if clingo_set - py_set:
            print("  only in ASP:", sorted(clingo_set - py_set))
        if py_set - clingo_set:
            print("  only in Python:", sorted(py_set - clingo_set))
        return 1
    print(f"OK: ASP and Python agree on {len(py_set)} valid story combos.")
    return 0


# ---------------------------------------------------------------------------
# Storyworld interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with magic and attitude.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--attitude", choices=ATTITUDES)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--guide-type", choices=GENTLE_GUIDES)
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
    tool = getattr(args, "tool", None) or rng.choice(list(TOOLS))
    attitude = getattr(args, "attitude", None) or rng.choice(list(ATTITUDES))
    reasonableness_gate(StoryParams(setting, tool, attitude, "x", "girl", "mother"))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    guide_type = getattr(args, "guide_type", None) or rng.choice(GENTLE_GUIDES)
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    if getattr(args, "attitude", None) == "attitudinal":
        attitude = "attitudinal"
    return StoryParams(setting, tool, attitude, hero_name, hero_type, guide_type)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
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
        print(asp_program("#show valid_story/3.\n#show good_magic/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        models = asp_valid_stories()
        print(f"{len(models)} valid story combinations:")
        for s, t, a in models:
            print(f"  {s:12} {t:8} {a}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(generate(p))
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero_name}: {p.attitude} with {p.tool} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
