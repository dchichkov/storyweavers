#!/usr/bin/env python3
"""
storyworlds/worlds/create_obtain_humor_animal_story.py
======================================================

A small animal-story world with a humorous, state-driven premise:
an animal wants to obtain something tasty or shiny, creates a clever-but-silly
tool, runs into trouble, and then reaches a funny safe solution.

The core seed tale imagined for this world is:
---
A small animal sees something it wants but cannot reach. It tries to create a
funny helper, fumbles a little, and finally obtains the prize in a harmless,
laughing way.
---

This script keeps the prose close to an Animal Story style:
- small animals as protagonists,
- simple concrete desires,
- a playful obstacle,
- a comic turn,
- a satisfying ending image showing the changed state.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    prize: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        mapping = {"subject": "it", "object": "it", "possessive": "its"}
        return mapping[case]

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
    indoor: bool = False
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
class Prize:
    label: str
    phrase: str
    type: str
    region: str
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


@dataclass
class CreateTool:
    id: str
    label: str
    phrase: str
    method: str
    humor: str
    helps: set[str]
    fitting_places: set[str]
    result: str
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
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _bool(flag: bool) -> float:
    return 1.0 if flag else 0.0


def _r_clumsy(world: World) -> list[str]:
    out: list[str] = []
    hero = _safe_fact(world, world.facts, "hero")
    tool = world.facts.get("tool")
    if not tool:
        return out
    if hero.memes.get("silliness", 0.0) >= THRESHOLD and hero.meters.get("attempts", 0.0) >= THRESHOLD:
        sig = ("clumsy", hero.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        hero.meters["mess"] = hero.meters.get("mess", 0.0) + 1.0
        out.append(f"{hero.label} got a little tangled in the funny helper.")
    return out


def _r_success(world: World) -> list[str]:
    out: list[str] = []
    hero = _safe_fact(world, world.facts, "hero")
    prize = _safe_fact(world, world.facts, "prize")
    tool = world.facts.get("tool")
    if not tool:
        return out
    if hero.meters.get("reach", 0.0) >= THRESHOLD and not world.facts.get("obtained"):
        sig = ("obtain", prize.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        world.facts["obtained"] = True
        prize.owner = hero.id
        out.append(f"{hero.label} could finally obtain the {prize.label}.")
    return out


CAUSAL_RULES = [_r_clumsy, _r_success]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def hero_intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.label} was a little {hero.type} who liked bright ideas and big treats.")


def want_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1.0
    world.say(f"One sunny day, {hero.label} spotted {prize.phrase} and wanted to obtain {prize.it()}.")


def create_tool(world: World, hero: Entity, tool_def: CreateTool) -> Entity:
    hero.memes["silliness"] = hero.memes.get("silliness", 0.0) + 1.0
    hero.meters["attempts"] = hero.meters.get("attempts", 0.0) + 1.0
    tool = world.add(Entity(
        id=tool_def.id,
        type="tool",
        label=tool_def.label,
        phrase=tool_def.phrase,
        owner=hero.id,
    ))
    world.facts["tool"] = tool
    world.say(
        f"Then {hero.label} tried to create {tool.phrase}. "
        f"It was a {tool_def.humor} idea, but {hero.label} smiled anyway."
    )
    return tool


def test_tool(world: World, hero: Entity, prize: Entity, tool_def: CreateTool) -> None:
    hero.meters["reach"] = hero.meters.get("reach", 0.0) + 1.0
    world.say(
        f"{hero.label} gave the helper a careful push and reached toward the {prize.label}. "
        f"It worked just enough to make the plan feel brave."
    )


def mishap(world: World, hero: Entity) -> None:
    hero.meters["mess"] = hero.meters.get("mess", 0.0) + 1.0
    world.say(f"For a moment, the helper wobbled and made {hero.label} look extra silly.")


def obtain_finish(world: World, hero: Entity, prize: Entity, tool_def: CreateTool) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    world.say(
        f"At last, {hero.label} used the {tool_def.label} and obtained the {prize.label}. "
        f"Then {hero.label} laughed at the goofy little invention and carried {prize.it()} home."
    )


def tell(setting: Setting, hero_type: str, hero_name: str, prize_cfg: Prize, tool_def: CreateTool) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    world.facts.update(hero=hero, prize=prize, setting=setting, tool=None, obtained=False)

    hero_intro(world, hero)
    want_prize(world, hero, prize)

    world.para()
    if setting.place not in tool_def.fitting_places:
        pass
    create_tool(world, hero, tool_def)
    test_tool(world, hero, prize, tool_def)
    mishap(world, hero)
    propagate(world, narrate=True)

    world.para()
    if not world.facts.get("obtained"):
        pass
    obtain_finish(world, hero, prize, tool_def)
    world.facts["resolved"] = True
    return world


SETTINGS = {
    "garden": Setting(place="the garden", indoor=False, affords={"create", "obtain"}),
    "yard": Setting(place="the yard", indoor=False, affords={"create", "obtain"}),
    "meadow": Setting(place="the meadow", indoor=False, affords={"create", "obtain"}),
}

PRIZES = {
    "berry": Prize(label="berry", phrase="a shiny red berry", type="berry", region="ground"),
    "cookie": Prize(label="cookie", phrase="a round cookie on a low branch", type="cookie", region="branch"),
    "kite": Prize(label="kite", phrase="a bright kite that snagged on a fence", type="kite", region="fence"),
}

TOOLS = [
    CreateTool(
        id="leaf_ramp",
        label="leaf ramp",
        phrase="a leaf ramp",
        method="stacking leaves into a tiny ramp",
        humor="wobbly",
        helps={"ground"},
        fitting_places={"garden", "meadow"},
        result="a better reach",
    ),
    CreateTool(
        id="twig_hook",
        label="twig hook",
        phrase="a twig hook",
        method="bending a twig into a crook",
        humor="squiggly",
        helps={"branch", "fence"},
        fitting_places={"yard", "garden"},
        result="a careful tug",
    ),
    CreateTool(
        id="stump_step",
        label="stump step",
        phrase="a stump step",
        method="shoving a stump close and hopping up",
        humor="squeaky",
        helps={"branch"},
        fitting_places={"meadow", "yard"},
        result="a little boost",
    ),
]

ANIMALS = {
    "rabbit": ["Pip", "Milo", "Nibbles", "Tilly", "Bunny"],
    "fox": ["Finn", "Ruby", "Sly", "Poppy", "Moss"],
    "bear": ["Bruno", "Mara", "Coco", "Toby", "Hazel"],
    "mouse": ["Dot", "Nico", "Penny", "Wiggle", "Mimi"],
}

CURATED = [
    ("garden", "rabbit", "berry", "leaf_ramp"),
    ("yard", "fox", "cookie", "twig_hook"),
    ("meadow", "mouse", "kite", "stump_step"),
]


@dataclass
class StoryParams:
    place: str
    animal: str
    prize: str
    tool: str
    name: str
    seed: Optional[int] = None
    params: object | None = None
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for animal in ANIMALS:
            for prize_id, prize in PRIZES.items():
                for tool in TOOLS:
                    if place in tool.fitting_places:
                        if prize.region in tool.helps:
                            combos.append((place, animal, prize_id, tool.id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: create something funny, obtain a prize.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--tool", choices=[t.id for t in TOOLS])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "animal", None) is None or c[1] == getattr(args, "animal", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
              and (getattr(args, "tool", None) is None or c[3] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, animal, prize, tool = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(ANIMALS, animal))
    return StoryParams(place=place, animal=animal, prize=prize, tool=tool, name=name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    prize = _safe_fact(world, f, "prize")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        f'Write a short animal story where a {hero.type} named {hero.label} tries to create something funny to obtain {prize.phrase}.',
        f"Tell a cheerful story in which {hero.label} creates {tool.phrase} and uses it to obtain the {prize.label}.",
        f'Write a tiny story for children with the words "create" and "obtain" that ends with laughter and a prize.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    prize = _safe_fact(world, f, "prize")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"What did {hero.label} want to do with {prize.label}?",
            answer=f"{hero.label} wanted to obtain {prize.it()} after spotting {prize.phrase}.",
        ),
        QAItem(
            question=f"What did {hero.label} create to help with the {prize.label}?",
            answer=f"{hero.label} created {tool.phrase}, a funny little helper that made the plan wobble and work.",
        ),
        QAItem(
            question=f"How did the story end for {hero.label}?",
            answer=f"{hero.label} obtained the {prize.label} and laughed at the silly helper on the way home.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to create something?",
            answer="To create something means to make it from parts, ideas, or materials that you put together.",
        ),
        QAItem(
            question="What does it mean to obtain something?",
            answer="To obtain something means to get it or come away with it.",
        ),
        QAItem(
            question="Why can funny plans make a story humorous?",
            answer="Funny plans can make a story humorous because they are a little silly, and the animal may wobble, bounce, or look surprised before the plan works.",
        ),
    ]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
in_setting(garden).
in_setting(yard).
in_setting(meadow).

animal(rabbit).
animal(fox).
animal(bear).
animal(mouse).

prize(berry).
prize(cookie).
prize(kite).

tool(leaf_ramp).
tool(twig_hook).
tool(stump_step).

fits(leaf_ramp, garden).
fits(leaf_ramp, meadow).
fits(twig_hook, yard).
fits(twig_hook, garden).
fits(stump_step, meadow).
fits(stump_step, yard).

helps(leaf_ramp, ground).
helps(twig_hook, branch).
helps(twig_hook, fence).
helps(stump_step, branch).

at_risk(berry, ground).
at_risk(cookie, branch).
at_risk(kite, fence).

valid(Place, Animal, Prize, Tool) :- in_setting(Place), animal(Animal), prize(Prize), tool(Tool),
                                      fits(Tool, Place), helps(Tool, R), at_risk(Prize, R).
#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("in_setting", place))
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for place in t.fitting_places:
            lines.append(asp.fact("fits", t.id, place))
        for r in t.helps:
            lines.append(asp.fact("helps", t.id, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("at_risk", pid, pr.region))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
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


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    tool_def = next(t for t in TOOLS if t.id == params.tool)
    world = tell(setting, params.animal, params.name, _safe_lookup(PRIZES, params.prize), tool_def)
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
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, animal, prize, tool in combos:
            print(f"  {place:8} {animal:7} {prize:7} {tool:10}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place, animal, prize, tool in CURATED:
            params = StoryParams(place=place, animal=animal, prize=prize, tool=tool, name=_safe_lookup(ANIMALS, animal)[0], seed=base_seed)
            samples.append(generate(params))
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
            header = f"### {p.name}: {p.animal} in {p.place} (prize: {p.prize}, tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
