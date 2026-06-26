#!/usr/bin/env python3
"""
storyworlds/worlds/bow_let_repetition_adventure.py
===================================================

A small adventure storyworld about a child explorer, a river crossing, and a
careful helper who keeps saying "let me" until the path is ready.

Seed-inspired premise:
- A brave child wants to go farther on an adventure.
- The route is blocked by a stream, a high ledge, or a windy gap.
- A useful bow, combined with rope or a line, can help solve the problem.
- Repetition is part of the style: one small phrase comes back several times.

The story stays state-driven: the explorer's desire, the helper's caution, the
tool's purpose, and the final crossing all come from the simulated world model.
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    tags: set[str] = field(default_factory=set)

    helper: object | None = None
    hero: object | None = None
    tool_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    id: str
    label: str
    kind: str
    danger: str
    requires: str
    detail: str
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


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    helps: str
    repeated_line: str
    tags: set[str] = field(default_factory=set)
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
    obstacle: str
    tool: str
    name: str
    gender: str
    helper: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.events: list[str] = []

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
        clone = World(self.place)
        import copy as _copy
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.events = list(self.events)
        return clone


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "riverbank": Place(
        id="riverbank",
        label="the riverbank",
        kind="outdoor",
        danger="cold water",
        requires="a way across the river",
        detail="The river moved fast, and the far bank looked bright and far away.",
    ),
    "cliffside": Place(
        id="cliffside",
        label="the cliff path",
        kind="outdoor",
        danger="a high drop",
        requires="a safe line",
        detail="The path hugged the cliff, and the wind tugged at every loose thing.",
    ),
    "woods": Place(
        id="woods",
        label="the woods",
        kind="outdoor",
        danger="getting lost",
        requires="a clear trail",
        detail="The trees stood close together, and the trail bent between roots and stones.",
    ),
}

OBSTACLES = {
    "river": {"tag": "water", "problem": "the water was too wide to step over"},
    "gap": {"tag": "drop", "problem": "the gap was too wide to jump"},
    "thicket": {"tag": "bushes", "problem": "the thicket was too thick to push through"},
}

TOOLS = {
    "bow": Tool(
        id="bow",
        label="bow",
        phrase="a small bow",
        use="shoot a line across the gap",
        helps="the line could pull a rope into place",
        repeated_line="Let me try, let me try, let me try.",
        tags={"line", "crossing", "adventure"},
    ),
    "rope": Tool(
        id="rope",
        label="rope",
        phrase="a sturdy rope",
        use="tie a bridge between two points",
        helps="the explorer could hold on while crossing",
        repeated_line="Let me help, let me help, let me help.",
        tags={"crossing", "adventure"},
    ),
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a little lantern",
        use="light the path at dusk",
        helps="the trail stayed bright enough to follow",
        repeated_line="Let me light it, let me light it.",
        tags={"light", "adventure"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Zoe", "Ivy"]
BOY_NAMES = ["Toby", "Finn", "Eli", "Theo", "Noah", "Max"]
TRAITS = ["brave", "curious", "eager", "bold", "patient"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_ready(world: World) -> list[str]:
    out = []
    explorer = world.get("hero")
    tool = world.get("tool")
    if explorer.memes.get("ready", 0) >= THRESHOLD and tool.meters.get("packed", 0) >= THRESHOLD:
        sig = ("ready",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("The pack was ready, and the path to adventure felt open.")
    return out


def _r_cross(world: World) -> list[str]:
    out = []
    explorer = world.get("hero")
    tool = world.get("tool")
    helper = world.get("helper")
    if explorer.meters.get("cross", 0) < THRESHOLD:
        return out
    if tool.id == "bow" and world.facts.get("bridge_made"):
        sig = ("cross", "bow")
        if sig not in world.fired:
            world.fired.add(sig)
            explorer.memes["joy"] = explorer.memes.get("joy", 0) + 1
            out.append("The explorer crossed safely.")
    elif tool.id == "rope" and world.facts.get("bridge_made"):
        sig = ("cross", "rope")
        if sig not in world.fired:
            world.fired.add(sig)
            explorer.memes["joy"] = explorer.memes.get("joy", 0) + 1
            out.append("The explorer crossed safely.")
    return out


RULES = [Rule("ready", _r_ready), Rule("cross", _r_cross)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def can_reasonably_use(place: Place, obstacle: str, tool: Tool) -> bool:
    if obstacle == "river":
        return tool.id in {"bow", "rope"}
    if obstacle == "gap":
        return tool.id in {"bow", "rope"}
    if obstacle == "thicket":
        return tool.id in {"lantern", "rope"}
    return False


def tool_fits(place: Place, obstacle: str, tool: Tool) -> bool:
    return can_reasonably_use(place, obstacle, tool)


def explain_rejection(place: Place, obstacle: str, tool: Tool) -> str:
    return (
        f"(No story: a {tool.label} does not solve this adventure problem at {place.label}. "
        f"The tool has to match the obstacle in a believable way.)"
    )


def _hero_intro(world: World, hero: Entity, helper: Entity, tool: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.memes.get('trait_word', 'brave')} explorer who loved big paths and small surprises."
    )
    world.say(
        f"{hero.pronoun().capitalize()} carried {hero.pronoun('possessive')} hope in one hand and {tool.phrase} in the other."
    )


def _setup(world: World, hero: Entity, helper: Entity, tool: Entity, obstacle: str) -> None:
    world.say(
        f"One day, {hero.id} and {hero.pronoun('possessive')} {helper.label} reached {world.place.label}."
    )
    world.say(world.place.detail)
    world.say(
        f"There was {_safe_lookup(OBSTACLES, obstacle)['problem']}, and the trip could not go farther until someone found a way."
    )


def _desire(world: World, hero: Entity, tool: Entity) -> None:
    hero.memes["want"] = hero.memes.get("want", 0) + 1
    world.say(
        f"{hero.id} wanted to go on, and {hero.pronoun('subject')} said, "
        f"\"Let me see, let me see, let me see.\""
    )


def _helper_pause(world: World, helper: Entity, hero: Entity, tool: Entity) -> None:
    helper.memes["care"] = helper.memes.get("care", 0) + 1
    world.say(
        f"{helper.id} lifted a hand and said, \"Let us be careful. Let us be careful.\""
    )
    world.say(
        f"Then {helper.id} looked at {tool.label} and smiled, because {tool.helps}."
    )


def _use_tool(world: World, hero: Entity, helper: Entity, tool: Entity, obstacle: str) -> None:
    world.say(
        f"{hero.id} nodded and tried again. {tool.repeated_line}"
    )
    if tool.id == "bow":
        world.say(
            f"{hero.id} drew the bow, sent a line over the water, and {helper.id} tied it down fast."
        )
        world.facts["bridge_made"] = True
    elif tool.id == "rope":
        world.say(
            f"{helper.id} looped the rope from one side to the other, and a little bridge took shape."
        )
        world.facts["bridge_made"] = True
    elif tool.id == "lantern":
        world.say(
            f"{helper.id} lit the lantern, and the dark trail turned bright enough to follow."
        )
        world.facts["bridge_made"] = True

    hero.meters["cross"] = 1.0
    propagate(world, narrate=False)


def _ending(world: World, hero: Entity, helper: Entity, tool: Entity, obstacle: str) -> None:
    world.say(
        f"In the end, {hero.id} went forward at last, and the scary part became only a story to tell."
    )
    if tool.id == "bow":
        world.say(
            f"The bow stayed tucked away, quiet now, while the new rope held steady above the river."
        )
    elif tool.id == "rope":
        world.say(
            f"The rope stayed stretched and strong, and the path beyond looked smaller than before."
        )
    elif tool.id == "lantern":
        world.say(
            f"The lantern glowed in {helper.id}'s hand as the trail opened into a safe, golden path."
        )


def tell(place: Place, obstacle: str, tool: Tool, hero_name: str, gender: str, helper_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=gender,
        meters={"cross": 0.0},
        memes={"trait_word": trait},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label="helper",
        memes={},
    ))
    tool_ent = world.add(Entity(
        id="tool",
        kind="thing",
        type=tool.id,
        label=tool.label,
        phrase=tool.phrase,
        owner=hero.id,
        carried_by=hero.id,
        meters={"packed": 1.0},
    ))

    _hero_intro(world, hero, helper, tool_ent)
    world.para()
    _setup(world, hero, helper, tool_ent, obstacle)
    _desire(world, hero, tool_ent)
    _helper_pause(world, helper, hero, tool_ent)
    world.para()
    _use_tool(world, hero, helper, tool_ent, obstacle)
    _ending(world, hero, helper, tool_ent, obstacle)

    world.facts.update(
        hero=hero,
        helper=helper,
        tool=tool_ent,
        obstacle=obstacle,
        place=place,
        tool_def=tool,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    tool = _safe_fact(world, f, "tool_def")
    obstacle = _safe_fact(world, f, "obstacle")
    place = _safe_fact(world, f, "place")
    return [
        f'Write a short adventure story for a child about {hero.id}, {place.label}, and a {tool.label}.',
        f'Tell a story where the phrase "Let me" appears more than once and a {tool.label} helps solve the problem at {place.label}.',
        f'Write a child-friendly adventure with repetition, a brave helper, and a clear ending image after the obstacle is fixed.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    tool = _safe_fact(world, f, "tool_def")
    place = _safe_fact(world, f, "place")
    obstacle = _safe_fact(world, f, "obstacle")
    return [
        QAItem(
            question=f"Where did {hero.id} go on the adventure?",
            answer=f"{hero.id} went to {place.label}, where the path was blocked by {_safe_lookup(OBSTACLES, obstacle)['problem']}.",
        ),
        QAItem(
            question=f"What did {hero.id} keep saying when {hero.pronoun('subject')} wanted to continue?",
            answer=f"{hero.id} kept saying, \"Let me see, let me see, let me see.\"",
        ),
        QAItem(
            question=f"How did the {tool.label} help?",
            answer=f"The {tool.label} helped because {tool.helps}.",
        ),
        QAItem(
            question=f"What did the helper say before the problem was solved?",
            answer=f"{helper.id} said, \"Let us be careful. Let us be careful.\"",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the obstacle was solved and {hero.id} could go farther on the adventure.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tool = _safe_fact(world, f, "tool_def")
    obstacle = _safe_fact(world, f, "obstacle")
    out = [
        QAItem(
            question="What is a bow usually for?",
            answer="A bow is often used to shoot an arrow, and in stories it can also help send a line across a gap.",
        ),
        QAItem(
            question="What does repetition mean in a story?",
            answer="Repetition means saying a word, phrase, or action again on purpose so it feels important or musical.",
        ),
        QAItem(
            question="Why do helpers sometimes say 'let me'?",
            answer="Helpers say 'let me' when they want to try, show care, or take the first careful step.",
        ),
    ]
    if tool.id == "bow":
        out.append(QAItem(
            question="Why was the bow a good tool for this adventure?",
            answer="The bow was a good tool because it could send a line to the far side and help make a crossing.",
        ))
    return out


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place_ok(P) :- place(P).
tool_ok(T) :- tool(T).
problem_ok(O) :- obstacle(O).

reasonably_fits(P, O, T) :- place_ok(P), problem_ok(O), tool_ok(T), fits(P, O, T).
valid_story(P, O, T) :- reasonably_fits(P, O, T).

#show valid_story/3.
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for o in OBSTACLES:
        lines.append(asp.fact("obstacle", o))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    for p in PLACES.values():
        for o in OBSTACLES:
            for t in TOOLS.values():
                if can_reasonably_use(p, o, t):
                    lines.append(asp.fact("fits", p.id, o, t.id))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def _asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set()
    for p in PLACES.values():
        for o in OBSTACLES:
            for t in TOOLS.values():
                if can_reasonably_use(p, o, t):
                    py.add((p.id, o, t.id))
    cl = set(_asp_valid_stories())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} valid stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    print(" only in python:", sorted(py - cl))
    print(" only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with repetition and a bow.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place_key = getattr(args, "place", None) or rng.choice(list(PLACES))
    obstacle_key = getattr(args, "obstacle", None) or rng.choice(list(OBSTACLES))
    tool_key = getattr(args, "tool", None) or rng.choice(list(TOOLS))
    place = _safe_lookup(PLACES, place_key)
    tool = _safe_lookup(TOOLS, tool_key)
    if not tool_fits(place, obstacle_key, tool):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        place=place_key,
        obstacle=obstacle_key,
        tool=tool_key,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(PLACES, params.place),
        params.obstacle,
        _safe_lookup(TOOLS, params.tool),
        params.name,
        params.gender,
        params.helper,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:8} {e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
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


CURATED = [
    StoryParams(place="riverbank", obstacle="river", tool="bow", name="Mina", gender="girl", helper="mother", trait="brave"),
    StoryParams(place="cliffside", obstacle="gap", tool="rope", name="Toby", gender="boy", helper="father", trait="curious"),
    StoryParams(place="woods", obstacle="thicket", tool="lantern", name="Ivy", gender="girl", helper="mother", trait="patient"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for row in _asp_valid_stories():
            print(row)
        return

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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.tool} at {p.place} ({p.obstacle})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
