#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/attach_cut_gerund_inner_monologue_magic_adventure.py
================================================================================================

A small adventure storyworld about a brave child, a magical attachment, and
a careful cutting choice that changes the path forward.

Seed premise:
---
A child is preparing a tiny adventure kit. A magic compass can be attached to a
satchel strap so it won't fall off on a windy trail. But the satchel is tangled
with a thorny ribbon, and the child must decide whether to cut it while keeping
the compass safe. The story includes the child's inner monologue and a gentle
magic helper that turns a messy problem into a confident plan.

World model:
---
- Physical meters track attachment, tangling, sharpness, and travel readiness.
- Emotional memes track worry, courage, relief, and wonder.
- "Attach" and "cut" are causal actions, not just words in a fixed paragraph.
- Inner monologue is narrated as a brief thought before each turning point.
- Magic changes the state only when the child uses the right object in the right way.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    attached_to: Optional[str] = None
    magical: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    obstacle: object | None = None
    parent: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str = "the forest path"
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
class Tool:
    id: str
    label: str
    phrase: str
    purpose: str
    magical: bool = False
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
class StoryParams:
    setting: str
    name: str
    gender: str
    parent: str
    tool: str
    obstacle: str
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
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_log: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "forest": Setting("the forest path", indoors=False),
    "ruins": Setting("the old stone ruins", indoors=False),
    "tower": Setting("the lantern tower", indoors=True),
}

TOOLS = {
    "compass": Tool(
        id="compass",
        label="magic compass",
        phrase="a tiny magic compass with a blue needle",
        purpose="guide the way",
        magical=True,
    ),
    "lantern": Tool(
        id="lantern",
        label="golden lantern",
        phrase="a small golden lantern that glowed like a star",
        purpose="light the way",
        magical=True,
    ),
    "rope": Tool(
        id="rope",
        label="braid of rope",
        phrase="a neat braid of rope for tying things together",
        purpose="hold things steady",
        magical=False,
    ),
}

OBSTACLES = {
    "thorn_ribbon": {
        "label": "thorny ribbon",
        "phrase": "a thorny ribbon snagged around the satchel strap",
        "tension": "tangled",
        "cut_action": "cut the ribbon",
        "risk": "scratch the satchel",
        "solution": "use a tiny charm to soften the thorns",
    },
    "knotted_vine": {
        "label": "knotted vine",
        "phrase": "a knotted vine wrapped around the pack handle",
        "tension": "tangled",
        "cut_action": "cut the vine",
        "risk": "jerk the pack loose",
        "solution": "cast a gentle untie spell",
    },
    "stiff_cord": {
        "label": "stiff cord",
        "phrase": "a stiff cord pinching the bundle shut",
        "tension": "tight",
        "cut_action": "cut the cord",
        "risk": "spill the supplies",
        "solution": "freeze the cord and snip it cleanly",
    },
}

GIRL_NAMES = ["Mira", "Nina", "Ada", "Lina", "Zara"]
BOY_NAMES = ["Owen", "Pax", "Jude", "Eli", "Toby"]


class WorldState:
    def __init__(self) -> None:
        self.values: dict[str, float] = {}

    def get(self, key: str) -> float:
        return self.values.get(key, 0.0)

    def add(self, key: str, amount: float) -> None:
        self.values[key] = self.get(key) + amount


def _m(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _mm(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for e in list(world.entities.values()):
            if e.attached_to and _m(e, "attached") < THRESHOLD:
                sig = ("attached", e.id, e.attached_to)
                if sig not in world.fired:
                    world.fired.add(sig)
                    e.meters["attached"] = 1.0
                    out.append(f"{e.label} stayed fastened in place.")
                    changed = True
            if _m(e, "cut") >= THRESHOLD and _m(e, "attached") >= THRESHOLD:
                sig = ("cut_free", e.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    e.meters["attached"] = 0.0
                    e.meters["cut_free"] = 1.0
                    out.append(f"The knot gave way and the path cleared.")
                    changed = True
            if _m(e, "magic_glow") >= THRESHOLD and _mm(e, "worry") >= THRESHOLD:
                sig = ("calm", e.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    e.memes["courage"] = e.memes.get("courage", 0.0) + 1.0
                    e.memes["worry"] = max(0.0, e.memes.get("worry", 0.0) - 1.0)
                    out.append(f"The glow made the worry feel smaller.")
                    changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


def make_story(world: World, hero: Entity, parent: Entity, tool: Entity, obstacle: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved small adventures and listened closely to every rustle on the trail."
    )
    world.say(
        f"{hero.pronoun().capitalize()} carried {hero.pronoun('possessive')} {tool.label}, because magic felt safest when it had a place to rest."
    )
    world.say(
        f"At {world.setting.place}, the group found {obstacle.phrase}."
    )
    world.para()

    hero.memes["worry"] = 1.0
    world.say(
        f"{hero.id} looked at the tangle and thought, 'If I pull too hard, the satchel might slip, and then the compass could be lost.'"
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted to be brave, but {hero.pronoun('possessive')} chest felt tight."
    )

    if obstacle.type == "thorn_ribbon":
        tool.attached_to = hero.id
        tool.meters["attached"] = 1.0
        world.say(
            f"{hero.pronoun('possessive').capitalize()} hands attached the magic compass to the strap first, so it would not wander off in the wind."
        )
        world.say("Then the hero took a careful breath.")
        obstacle.meters["tangled"] = 1.0
        hero.meters["sharp"] = 0.0
        if world.facts.get("use_magic"):
            hero.meters["magic_glow"] = 1.0
            world.say(
                f"{hero.id} whispered a tiny spell and imagined the thorns growing sleepy."
            )
        world.say(
            f"With one careful cut, {hero.id} could {obstacle['cut_action']} without making the bag tear."
        )
        obstacle.meters["cut"] = 1.0
        hero.memes["courage"] = 1.0
        propagate(world, narrate=True)
        world.say(
            f"{hero.id} smiled as the compass stayed fixed and the ribbon fell away like a shed leaf."
        )
    elif obstacle.type == "knotted_vine":
        world.say(
            f"{hero.id} touched the vine and thought, 'I can solve this slowly. Slow is still brave.'"
        )
        world.say(
            f"{parent.pronoun().capitalize()} nodded, and the child used a small magic glow to untie the knot before cutting anything."
        )
        obstacle.meters["cut"] = 1.0
        obstacle.meters["tangled"] = 0.0
        hero.meters["magic_glow"] = 1.0
        propagate(world, narrate=True)
        world.say(
            f"At last the vine loosened, and the pack handle swung free in the child’s hands."
        )
    else:
        world.say(
            f"{hero.id} wondered if the bundle should be opened from the side instead of ripped apart."
        )
        world.say(
            f"{parent.id} agreed, and the child used a neat freeze spell before making the cut."
        )
        obstacle.meters["cut"] = 1.0
        hero.meters["magic_glow"] = 1.0
        propagate(world, narrate=True)
        world.say(
            f"The supplies stayed snug, and the trail ahead looked ready for marching feet."
        )

    world.para()
    hero.memes["worry"] = 0.0
    hero.memes["relief"] = 1.0
    world.say(
        f"{hero.id} felt light again, because the tool was safe, the obstacle was gone, and the adventure could go on."
    )
    world.say(
        f"By the end, the path felt wider, and {hero.id} walked forward with a bright, steady smile."
    )


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"sharp": 0.0},
        memes={"worry": 0.0, "courage": 0.0, "relief": 0.0},
    ))
    parent = world.add(Entity(
        id=params.parent,
        kind="character",
        type=params.parent,
        label=params.parent,
    ))
    tool_def = _safe_lookup(TOOLS, params.tool)
    tool = world.add(Entity(
        id=tool_def.id,
        type="tool",
        label=tool_def.label,
        phrase=tool_def.phrase,
        owner=hero.id,
        caretaker=parent.id,
        magical=tool_def.magical,
        meters={"attached": 0.0},
    ))
    obstacle_def = _safe_lookup(OBSTACLES, params.obstacle)
    obstacle = world.add(Entity(
        id=params.obstacle,
        type=params.obstacle,
        label=obstacle_def["label"],
        phrase=obstacle_def["phrase"],
        meters={"tangled": 1.0},
    ))

    world.facts.update(use_magic=tool.magical, hero=hero, parent=parent, tool=tool, obstacle=obstacle)
    make_story(world, hero, parent, tool, obstacle)
    return world


def story_variant(seed: int) -> StoryParams:
    rng = random.Random(seed)
    setting = rng.choice(list(SETTINGS))
    gender = rng.choice(["girl", "boy"])
    name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = rng.choice(["mother", "father"])
    tool = rng.choice(list(TOOLS))
    obstacle = rng.choice(list(OBSTACLES))
    return StoryParams(setting=setting, name=name, gender=gender, parent=parent, tool=tool, obstacle=obstacle, seed=seed)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    obstacle = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "obstacle")
    return [
        f"Write a short adventure story for a child named {hero.id} that includes a magical {tool.label} and a careful cut.",
        f"Tell a gentle story where {hero.id} uses inner monologue to solve a {obstacle.label} problem on the trail.",
        f"Create a child-friendly adventure with magic, worry, and relief, ending with the {tool.label} safely attached.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    parent = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    obstacle = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "obstacle")
    return [
        QAItem(
            question=f"What did {hero.id} attach before the cutting part of the adventure?",
            answer=f"{hero.id} attached the {tool.label} to keep it from getting lost during the trip.",
        ),
        QAItem(
            question=f"Why did {hero.id} think carefully before cutting the {obstacle.label}?",
            answer=f"{hero.id} was worried that a rough cut could harm the bag or spill the supplies, so {hero.pronoun()} chose a careful plan.",
        ),
        QAItem(
            question=f"Who helped {hero.id} stay calm while solving the problem?",
            answer=f"{parent.id} helped by nodding and staying close while {hero.id} worked through the problem.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does attach mean?",
            answer="To attach something means to fasten it so it stays connected to something else.",
        ),
        QAItem(
            question="Why should a child cut carefully near a bag or strap?",
            answer="A careful cut helps keep the bag, strap, and things inside safe.",
        ),
        QAItem(
            question="What can magic do in a story like this?",
            answer="Magic can help solve a problem in a gentle way, like calming a tangle or making a knot easier to loosen.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the voice of a character’s own thoughts inside their head.",
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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.attached_to:
            bits.append(f"attached_to={e.attached_to}")
        if e.magical:
            bits.append("magical=True")
        lines.append(f"{e.id}: {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
tool(T) :- tool_id(T).
obstacle(O) :- obstacle_id(O).

needs_attach(H,T) :- hero(H), tool(T), magical(T).
needs_cut(H,O) :- hero(H), obstacle(O), tangled(O).

safe_solution(H,T,O) :- needs_attach(H,T), needs_cut(H,O), magical(T).

valid_story(Setting, Tool, Obstacle) :- setting_id(Setting), tool_id(Tool), obstacle_id(Obstacle),
                                       valid_pair(Tool, Obstacle).

valid_pair(compass, thorn_ribbon).
valid_pair(lantern, knotted_vine).
valid_pair(rope, stiff_cord).

#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting_id", sid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool_id", tid))
        if t.magical:
            lines.append(asp.fact("magical", tid))
    for oid in OBSTACLES:
        lines.append(asp.fact("obstacle_id", oid))
        lines.append(asp.fact("tangled", oid))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: attach, cut, inner monologue, and magic.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
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
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    tool = getattr(args, "tool", None) or rng.choice(list(TOOLS))
    obstacle = getattr(args, "obstacle", None) or rng.choice(list(OBSTACLES))
    if getattr(args, "tool", None) and getattr(args, "obstacle", None):
        if (getattr(args, "tool", None), getattr(args, "obstacle", None)) not in {("compass", "thorn_ribbon"), ("lantern", "knotted_vine"), ("rope", "stiff_cord")}:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(setting=setting, name=name, gender=gender, parent=parent, tool=tool, obstacle=obstacle)


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


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_stories())
    python_set = {
        (s, t, o)
        for s in SETTINGS
        for t in TOOLS
        for o in OBSTACLES
        if (t, o) in {("compass", "thorn_ribbon"), ("lantern", "knotted_vine"), ("rope", "stiff_cord")}
    }
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python ({len(clingo_set)} story combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(setting="forest", name="Mira", gender="girl", parent="mother", tool="compass", obstacle="thorn_ribbon"),
    StoryParams(setting="ruins", name="Owen", gender="boy", parent="father", tool="lantern", obstacle="knotted_vine"),
    StoryParams(setting="tower", name="Ada", gender="girl", parent="mother", tool="rope", obstacle="stiff_cord"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for row in asp_valid_stories():
            print(row)
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
            header = f"### {p.name}: {p.tool} vs {p.obstacle} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
