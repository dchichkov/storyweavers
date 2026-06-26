#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/excess_functional_kindness_lesson_learned_friendship_superhero.py
====================================================================================================

A small superhero-story world about excess kindness, functional kindness, friendship,
and the lesson learned when help becomes effective.

The seed-inspired premise:
- A young superhero wants to help everyone at once.
- Their kindness is real, but it becomes excess: too many promises, too many jobs,
  and not enough clear action.
- A friend shows a functional way to help: pick one job, do it well, and work together.
- The ending proves the change through a saved day and a stronger friendship.

This script is standalone and follows the Storyweavers storyworld contract.
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    place: str = "the city square"
    weather: str = "bright"
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
class Challenge:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    scene: str
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
    function: str
    helps_with: set[str]
    plural: bool = False
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _r_overhelp(world: World) -> list[str]:
    out: list[str] = []
    hero = _safe_fact(world, world.facts, "hero")
    helper = world.get(hero.id)
    if helper.memes.get("excess_help", 0.0) < THRESHOLD:
        return out
    sig = ("overhelp", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["confusion"] = helper.memes.get("confusion", 0.0) + 1
    out.append("The hero's extra offers made the plan wobble.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get(world.facts["hero"].id)
    friend = world.get(world.facts["friend"].id)
    if hero.memes.get("focus", 0.0) < THRESHOLD:
        return out
    sig = ("teamwork", hero.id, friend.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["confidence"] = hero.memes.get("confidence", 0.0) + 1
    friend.memes["trust"] = friend.memes.get("trust", 0.0) + 1
    out.append("The two friends found a better way to help together.")
    return out


CAUSAL_RULES = [_r_overhelp, _r_teamwork]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            texts = rule(world)
            if texts:
                changed = True
                produced.extend(texts)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_outcome(world: World, hero: Entity, friend: Entity, challenge: Challenge) -> dict:
    sim = world.copy()
    sim.get(hero.id).memes["excess_help"] = 1.0
    propagate(sim, narrate=False)
    return {
        "confused": sim.get(hero.id).memes.get("confusion", 0.0) >= THRESHOLD,
        "trusted": sim.get(friend.id).memes.get("trust", 0.0) >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{hero.id} was a young superhero with a shiny cape and a big heart. "
        f"{hero.pronoun().capitalize()} loved helping people, and {friend.id} liked being nearby when the city needed help."
    )


def setup_need(world: World, hero: Entity, friend: Entity, challenge: Challenge) -> None:
    world.say(
        f"One afternoon at {world.setting.place}, {challenge.scene}. "
        f"{friend.id} saw the trouble first and called for {hero.id}."
    )


def overdo_kindness(world: World, hero: Entity, friend: Entity, challenge: Challenge) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    hero.memes["excess_help"] = hero.memes.get("excess_help", 0.0) + 1
    world.say(
        f"{hero.id} rushed over and offered to do everything at once. "
        f"{hero.pronoun().capitalize()} tried to {challenge.rush}, but the extra promises made the work pile up."
    )
    propagate(world)


def lesson_turn(world: World, hero: Entity, friend: Entity, challenge: Challenge, tool: Tool) -> None:
    hero.memes["lesson_ready"] = hero.memes.get("lesson_ready", 0.0) + 1
    world.say(
        f"{friend.id} pointed to the mess and said, 'Kindness works best when it is functional. "
        f"Pick one job, and let me do the other.'"
    )
    world.say(
        f"{hero.id} took a breath, listened, and chose a clear plan: use {tool.label} for the hardest part."
    )
    hero.memes["focus"] = hero.memes.get("focus", 0.0) + 1
    propagate(world)


def solve(world: World, hero: Entity, friend: Entity, challenge: Challenge, tool: Tool) -> None:
    hero.memes["lesson_learned"] = 1.0
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1
    world.say(
        f"Then {hero.id} used {tool.label} exactly where it was needed. "
        f"{friend.id} handled the rest, and together they fixed the problem before the crowd grew worried."
    )
    world.say(
        f"By the end, {challenge.gerund} had become a job for two friends, not a storm of excess help."
    )


def ending(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{hero.id} smiled under {hero.pronoun('possessive')} cape and promised to remember the lesson. "
        f"{friend.id} smiled back, because real friendship made every helpful plan stronger."
    )


SETTINGS = {
    "city_square": Setting(place="the city square", weather="bright", affords={"rescue", "repair"}),
    "rooftop": Setting(place="the rooftop garden", weather="windy", affords={"rescue"}),
    "harbor": Setting(place="the harbor walk", weather="breezy", affords={"repair", "rescue"}),
}

CHALLENGES = {
    "lost_balloon": Challenge(
        id="lost_balloon",
        verb="catch the balloon",
        gerund="catching the balloon",
        rush="grab every rope and chair at once",
        risk="the balloon drifting away",
        scene="a bundle of festival balloons tangled around a lamppost",
        keyword="balloon",
        tags={"sky", "wind"},
    ),
    "broken_bridge_sign": Challenge(
        id="broken_bridge_sign",
        verb="fix the bridge sign",
        gerund="fixing the bridge sign",
        rush="hold every plank and nail in the air",
        risk="the sign staying broken",
        scene="a bridge sign had snapped loose and was hanging crookedly",
        keyword="sign",
        tags={"repair", "wood"},
    ),
    "stuck_cat": Challenge(
        id="stuck_cat",
        verb="help the cat down",
        gerund="helping the cat down",
        rush="try every ladder and blanket together",
        risk="the cat getting more scared",
        scene="a small cat had climbed onto a safe ledge and was too nervous to jump",
        keyword="cat",
        tags={"rescue", "gentle"},
    ),
}

TOOLS = {
    "magnet_hook": Tool(
        id="magnet_hook",
        label="a magnet hook",
        phrase="a shiny magnet hook",
        function="pull metal things down safely",
        helps_with={"lost_balloon", "broken_bridge_sign"},
    ),
    "soft_blanket": Tool(
        id="soft_blanket",
        label="a soft blanket",
        phrase="a soft blanket",
        function="make a scared creature feel safe",
        helps_with={"stuck_cat"},
    ),
    "tool_belt": Tool(
        id="tool_belt",
        label="the tool belt",
        phrase="the tool belt",
        function="carry one useful tool at a time",
        helps_with={"broken_bridge_sign", "lost_balloon", "stuck_cat"},
    ),
}

HERO_NAMES = ["Nova", "Ray", "Spark", "Mira", "Dash", "Tala"]
FRIEND_NAMES = ["Bluejay", "Comet", "Penny", "Zig", "Jules", "Wren"]
TRAITS = ["brave", "kind", "bright", "gentle", "quick"]


@dataclass
class StoryParams:
    setting: str
    challenge: str
    tool: str
    hero_name: str
    friend_name: str
    hero_trait: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_id, setting in SETTINGS.items():
        for c_id, challenge in CHALLENGES.items():
            if c_id not in setting.affords:
                continue
            for t_id, tool in TOOLS.items():
                if c_id in tool.helps_with:
                    combos.append((s_id, c_id, t_id))
    return combos


def explain_rejection(setting: Setting, challenge: Challenge, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not fit this challenge in {setting.place}. "
        f"The story needs a functional tool that really helps with {challenge.gerund}.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world about excess kindness and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--trait")
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
    if getattr(args, "setting", None) and getattr(args, "challenge", None) and getattr(args, "tool", None):
        s, c, t = _safe_lookup(SETTINGS, getattr(args, "setting", None)), _safe_lookup(CHALLENGES, getattr(args, "challenge", None)), _safe_lookup(TOOLS, getattr(args, "tool", None))
        if c.id not in s.affords or c.id not in t.helps_with:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in valid_combos()
        if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
        and (getattr(args, "challenge", None) is None or c[1] == getattr(args, "challenge", None))
        and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, challenge, tool = rng.choice(list(combos))
    return StoryParams(
        setting=setting,
        challenge=challenge,
        tool=tool,
        hero_name=getattr(args, "hero_name", None) or rng.choice(HERO_NAMES),
        friend_name=getattr(args, "friend_name", None) or rng.choice(FRIEND_NAMES),
        hero_trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    challenge = _safe_lookup(CHALLENGES, params.challenge)
    tool = _safe_lookup(TOOLS, params.tool)
    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type="girl", traits=[params.hero_trait, "superhero"]))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="boy", traits=["friendly"]))
    world.facts.update(hero=hero, friend=friend, challenge=challenge, tool=tool)
    introduce(world, hero, friend)
    world.para()
    setup_need(world, hero, friend, challenge)
    overdo_kindness(world, hero, friend, challenge)
    world.para()
    lesson_turn(world, hero, friend, challenge, tool)
    solve(world, hero, friend, challenge, tool)
    ending(world, hero, friend)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short superhero story for a child about a hero whose kindness starts out too big and becomes functional with help from a friend.",
        f"Tell a gentle superhero story where {f['hero'].id} learns a lesson about using {(f.get('tool') or next(iter(TOOLS.values()))).label} in a useful way.",
        f"Write a friendship story with a superhero, a challenge, and a clear lesson learned at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, challenge, tool = f["hero"], f["friend"], f["challenge"], (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"Who is the story mainly about?",
            answer=f"The story is mainly about {hero.id}, a young superhero who learns how to make kindness functional.",
        ),
        QAItem(
            question=f"What made {hero.id}'s kindness turn into a problem at first?",
            answer=f"{hero.id} tried to help with excess help all at once, which made the plan wobble instead of working cleanly.",
        ),
        QAItem(
            question=f"What did {friend.id} tell {hero.id} to do?",
            answer=f"{friend.id} told {hero.id} to pick one job, use {tool.label} for the hard part, and let the plan stay simple.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn by the end?",
            answer=f"{hero.id} learned that kindness is strongest when it is functional, focused, and shared with a friend.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {friend.id}?",
            answer=f"They fixed the problem together, and their friendship grew because they worked as a team.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "kindness": [
        QAItem(
            question="What is kindness?",
            answer="Kindness means doing caring things for others, like helping, sharing, and speaking gently.",
        )
    ],
    "friendship": [
        QAItem(
            question="What is friendship?",
            answer="Friendship is a caring connection between people who help each other and enjoy being together.",
        )
    ],
    "lesson": [
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="To learn a lesson means to understand something important that helps you do better next time.",
        )
    ],
    "functional": [
        QAItem(
            question="What does functional mean?",
            answer="Functional means something works the way it should and helps get the job done.",
        )
    ],
    "excess": [
        QAItem(
            question="What does excess mean?",
            answer="Excess means too much of something, more than is useful or needed.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return (
        WORLD_KNOWLEDGE["kindness"]
        + WORLD_KNOWLEDGE["friendship"]
        + WORLD_KNOWLEDGE["lesson"]
        + WORLD_KNOWLEDGE["functional"]
        + WORLD_KNOWLEDGE["excess"]
    )


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- setting_fact(S).
challenge(C) :- challenge_fact(C).
tool(T) :- tool_fact(T).

valid(S,C,T) :- setting_fact(S), challenge_fact(C), tool_fact(T), affords(S,C), helps(T,C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting_fact", sid))
        for c in sorted(s.affords):
            lines.append(asp.fact("affords", sid, c))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge_fact", cid))
        lines.append(asp.fact("scene", cid, c.scene))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool_fact", tid))
        for c in sorted(t.helps_with):
            lines.append(asp.fact("helps", tid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


CURATED = [
    StoryParams("city_square", "lost_balloon", "magnet_hook", "Nova", "Bluejay", "brave"),
    StoryParams("harbor", "broken_bridge_sign", "tool_belt", "Spark", "Wren", "kind"),
    StoryParams("rooftop", "stuck_cat", "soft_blanket", "Mira", "Jules", "gentle"),
]


def generate(params: StoryParams) -> StorySample:
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, challenge, tool) combos:\n")
        for row in combos:
            print("  ", row)
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
            header = f"### {p.hero_name}: {p.challenge} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
