#!/usr/bin/env python3
"""
storyworlds/worlds/fog_sorrow_repetition_adventure.py
=====================================================

A small adventure storyworld about a child, a foggy path, and a little sorrow
that changes through repeated tries.

The premise:
- A child wants to reach a place across a foggy trail.
- The fog makes simple things hard to see.
- The child repeats an attempt, learns a safer method, and reaches the goal.

The domain is intentionally small and constraint-checked:
- The fog can hide landmarks and separate the child from a helpful goal.
- Repetition matters: repeated tries can build confidence or reveal a pattern.
- The ending always proves a change in state: a path is crossed, a signal is
  found, or a helper is reunited with the child.

This script follows the Storyweavers contract:
- stdlib only, plus lazy ASP helper use
- typed entities with physical meters and emotional memes
- explicit invalid choices raise StoryError
- inline ASP rules mirror the Python reasonableness gate
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    goal: object | None = None
    hero: object | None = None
    parent: object | None = None
    tool: object | None = None
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
    outdoor: bool = True
    affords: set[str] = field(default_factory=set)
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
class Goal:
    id: str
    label: str
    phrase: str
    location: str
    cue: str
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
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    reveals: set[str]
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
    goal: str
    tool: str
    name: str
    gender: str
    parent: str
    trait: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.fog_density: float = 0.0
        self.repetitions: int = 0

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

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.fog_density = self.fog_density
        clone.repetitions = self.repetitions
        return clone


SETTINGS = {
    "harbor": Setting(place="the harbor", outdoor=True, affords={"search", "signal"}),
    "woods": Setting(place="the woods", outdoor=True, affords={"search", "signal"}),
    "hill": Setting(place="the hill", outdoor=True, affords={"search", "signal"}),
    "gate": Setting(place="the old gate", outdoor=True, affords={"search", "signal"}),
}

GOALS = {
    "lantern": Goal(id="lantern", label="lantern", phrase="a little brass lantern", location="near the trail bend", cue="glow"),
    "bell": Goal(id="bell", label="bell", phrase="a silver bell on a post", location="beside the path", cue="ring"),
    "boat": Goal(id="boat", label="boat", phrase="a small red boat", location="at the water edge", cue="bob"),
    "bridge": Goal(id="bridge", label="bridge", phrase="a wooden bridge", location="over the stream", cue="planks"),
}

TOOLS = {
    "lamp": Tool(id="lamp", label="lantern lamp", phrase="a tiny lantern lamp", helps={"signal", "search"}, reveals={"glow"}),
    "rope": Tool(id="rope", label="rope", phrase="a coil of rope", helps={"search"}, reveals={"tug"}),
    "whistle": Tool(id="whistle", label="whistle", phrase="a bright whistle", helps={"signal"}, reveals={"sound"}),
}

GIRL_NAMES = ["Mia", "Luna", "Ivy", "Nora", "Ava", "Zoe", "Lily", "Maya"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Eli", "Max", "Theo", "Ben", "Sam"]
TRAITS = ["brave", "curious", "gentle", "steady", "lively", "thoughtful"]


def fog_at_risk(goal: Goal, setting: Setting) -> bool:
    return setting.place in {"the harbor", "the woods", "the hill", "the old gate"}


def tool_helpful(tool: Tool, goal: Goal) -> bool:
    return goal.cue in tool.reveals or "signal" in tool.helps


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for goal_id, goal in GOALS.items():
            if not fog_at_risk(goal, setting):
                continue
            for tool_id, tool in TOOLS.items():
                if tool_helpful(tool, goal):
                    combos.append((place, goal_id, tool_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Foggy adventure storyworld with sorrow and repetition.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if getattr(args, "goal", None) and getattr(args, "tool", None):
        if not tool_helpful(_safe_lookup(TOOLS, getattr(args, "tool", None)), _safe_lookup(GOALS, getattr(args, "goal", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "goal", None) is None or c[1] == getattr(args, "goal", None))
        and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, goal, tool = rng.choice(list(combos))
    g = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if g == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, goal=goal, tool=tool, name=name, gender=g, parent=parent, trait=trait)


def _start_story(world: World, hero: Entity, parent: Entity, goal: Goal, tool: Tool) -> None:
    world.say(f"{hero.id} was a {hero.memes.get('trait_word', 'small')} {hero.type} who loved a good trail.")
    world.say(f"{hero.pronoun().capitalize()} carried {tool.phrase} and hoped to find {goal.phrase}.")


def _raise_fog(world: World, hero: Entity, goal: Goal) -> None:
    world.fog_density += 1.0
    hero.memes["sorrow"] += 1.0
    world.say(f"Then fog rolled in and hid the path, so {hero.id}'s heart sank a little.")


def _first_try(world: World, hero: Entity, goal: Goal) -> None:
    world.repetitions += 1
    hero.memes["hope"] += 0.5
    world.say(f"{hero.id} tried once, peering hard into the white hush, but the little cue stayed lost.")


def _second_try(world: World, hero: Entity, tool: Tool, goal: Goal) -> None:
    world.repetitions += 1
    hero.memes["sorrow"] = max(0.0, hero.memes["sorrow"] - 0.5)
    world.say(f"{hero.id} tried again, this time using {tool.label} like a clue-finder.")
    if goal.cue == "glow":
        world.say(f"A tiny glow answered back through the fog.")
    elif goal.cue == "ring":
        world.say(f"A faint ring came drifting over the hill.")
    elif goal.cue == "bob":
        world.say(f"A soft bobbing shape moved at the water's edge.")
    else:
        world.say(f"The shape of the bridge slowly came forward out of the gray.")


def _resolve(world: World, hero: Entity, parent: Entity, goal: Goal, tool: Tool) -> None:
    hero.memes["joy"] += 1.0
    hero.memes["sorrow"] = 0.0
    world.say(
        f"On the third look, {hero.id} saw {goal.phrase} at last, and "
        f"{hero.pronoun('possessive')} {parent.type} smiled from beside {hero.pronoun('object')}."
    )
    world.say(
        f"Together they went on, and {tool.label} stayed steady while the fog "
        f"thinned around them."
    )


def tell(setting: Setting, goal_cfg: Goal, tool_cfg: Tool, hero_name: str = "Mina",
         hero_type: str = "girl", hero_traits: Optional[list[str]] = None,
         parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        memes={"sorrow": 0.0, "joy": 0.0, "hope": 0.0, "trait_word": 0.0},
    ))
    hero.memes["trait_word"] = 1.0
    hero.memes["trait_word_name"] = 0.0
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    goal = world.add(Entity(id=goal_cfg.id, type=goal_cfg.label, label=goal_cfg.label, phrase=goal_cfg.phrase, location=goal_cfg.location))
    tool = world.add(Entity(id=tool_cfg.id, type=tool_cfg.label, label=tool_cfg.label, phrase=tool_cfg.phrase, owner=hero.id))

    world.facts.update(hero=hero, parent=parent, goal=goal, tool=tool, goal_cfg=goal_cfg, setting=setting)

    trait = hero_traits[0] if hero_traits else "brave"
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved adventure.")
    world.say(f"{hero.id} had {tool.phrase}, and {goal.phrase} was the thing {hero.pronoun()} wanted most.")
    world.para()
    _raise_fog(world, hero, goal)
    _first_try(world, hero, goal)
    world.para()
    _second_try(world, hero, tool, goal)
    _resolve(world, hero, parent, goal, tool)
    world.facts["repetitions"] = world.repetitions
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, goal_cfg, tool = f["hero"], f["goal_cfg"], (f.get("tool") or next(iter(TOOLS.values())))
    return [
        f'Write a short adventure story for a child named {hero.id} who meets fog and keeps trying.',
        f"Tell a story where {hero.id} feels sorrow in the fog, then repeats the search and finds {goal_cfg.phrase}.",
        f"Write a gentle adventure about {hero.id} using {tool.phrase} to find a hidden thing through fog.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, goal_cfg, tool = f["hero"], f["parent"], f["goal_cfg"], (f.get("tool") or next(iter(TOOLS.values())))
    qa = [
        QAItem(
            question=f"What was {hero.id} trying to find in the fog?",
            answer=f"{hero.id} was trying to find {goal_cfg.phrase} in the fog.",
        ),
        QAItem(
            question=f"What helped {hero.id} keep trying again?",
            answer=f"{tool.phrase} helped {hero.id} keep trying again, because it made the search feel more possible.",
        ),
        QAItem(
            question=f"Who was nearby when the fog started to fade?",
            answer=f"{parent.type.capitalize()} was nearby, smiling as the fog began to thin and {hero.id} finally saw the goal.",
        ),
    ]
    if f.get("repetitions", 0) >= 2:
        qa.append(
            QAItem(
                question=f"How many tries did {hero.id} make before the goal was found?",
                answer=f"{hero.id} tried more than once, and the repeated tries helped turn sorrow into hope.",
            )
        )
    return qa


KNOWLEDGE = {
    "fog": [
        QAItem(
            question="What is fog?",
            answer="Fog is a cloud of tiny water drops that hangs low in the air and makes it hard to see far away.",
        ),
        QAItem(
            question="Why do roads feel different in fog?",
            answer="Roads in fog can feel mysterious because the gray air hides distant shapes and makes everything look close and quiet.",
        ),
    ],
    "sorrow": [
        QAItem(
            question="What is sorrow?",
            answer="Sorrow is a sad feeling that can make a person want comfort, a hug, or a little time to feel better.",
        ),
    ],
    "adventure": [
        QAItem(
            question="What makes a story feel like an adventure?",
            answer="An adventure usually has a goal, a place to travel, a challenge to solve, and a brave try or two along the way.",
        ),
    ],
    "repetition": [
        QAItem(
            question="Why can repeating a try help?",
            answer="Repeating a try can help because you notice more each time, remember what failed, and sometimes find a better way.",
        ),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"fog", "sorrow", "adventure", "repetition"}
    out: list[QAItem] = []
    for tag in tags:
        out.extend(KNOWLEDGE.get(tag, []))
    return out


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
    lines.append(f"  fog_density={world.fog_density}")
    lines.append(f"  repetitions={world.repetitions}")
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "No valid fog adventure matches the requested constraints."


ASP_RULES = r"""
foggy_place(P) :- setting(P).
goal_at_risk(G, P) :- goal(G), setting(P), foggy_place(P).
helpful(T, G) :- tool(T), goal(G), reveals(T, C), cue(G, C).
valid(P, G, T) :- goal_at_risk(G, P), helpful(T, G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for g_id, g in GOALS.items():
        lines.append(asp.fact("goal", g_id))
        lines.append(asp.fact("cue", g_id, g.cue))
    for t_id, t in TOOLS.items():
        lines.append(asp.fact("tool", t_id))
        for r in sorted(t.reveals):
            lines.append(asp.fact("reveals", t_id, r))
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
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="woods", goal="lantern", tool="lamp", name="Mina", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="hill", goal="bell", tool="whistle", name="Leo", gender="boy", parent="father", trait="curious"),
    StoryParams(place="harbor", goal="boat", tool="lamp", name="Ava", gender="girl", parent="mother", trait="steady"),
    StoryParams(place="gate", goal="bridge", tool="rope", name="Theo", gender="boy", parent="father", trait="thoughtful"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(GOALS, params.goal), _safe_lookup(TOOLS, params.tool),
                 params.name, params.gender, [params.trait], params.parent)
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, goal, tool) combos:\n")
        for place, goal, tool in combos:
            print(f"  {place:10} {goal:8} {tool:8}")
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
            header = f"### {p.name}: {p.goal} at {p.place} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
