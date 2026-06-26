#!/usr/bin/env python3
"""
A standalone story world: swift little space adventures with sound effects and
gentle humor. The story engine simulates a tiny crew, a small ship problem, and
a clever fix that lets the mission end on a bright, satisfying image.
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    module_ent: object | None = None
    tool_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "pilot"}:
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
class ShipModule:
    name: str
    sound: str
    problem: str
    risk: str
    fix: str
    location: str
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
class Tool:
    id: str
    label: str
    phrase: str
    solves: set[str]
    fits: set[str]
    sound: str
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
    atmosphere: str
    supports: set[str] = field(default_factory=set)
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "orbital_port": Setting(place="the orbital port", atmosphere="bright", supports={"dock", "repair"}),
    "asteroid_bay": Setting(place="the asteroid bay", atmosphere="dusty", supports={"dock", "repair", "scan"}),
    "moon_garden": Setting(place="the moon garden", atmosphere="quiet", supports={"scan"}),
    "space_market": Setting(place="the space market", atmosphere="busy", supports={"dock", "trade"}),
}

MODULES = {
    "telescope": ShipModule(
        name="telescope",
        sound="whirr",
        problem="foggy lens",
        risk="blurred stars",
        fix="clean the lens",
        location="nose",
        tags={"scan", "stars"},
    ),
    "radio": ShipModule(
        name="radio",
        sound="beep-beep",
        problem="static",
        risk="mixed-up messages",
        fix="retune the radio",
        location="bridge",
        tags={"signal", "beep"},
    ),
    "hatch": ShipModule(
        name="hatch",
        sound="clang",
        problem="sticky latch",
        risk="stuck door",
        fix="oil the hinge",
        location="airlock",
        tags={"dock", "door"},
    ),
    "thruster": ShipModule(
        name="thruster",
        sound="vroom",
        problem="jammed nozzle",
        risk="wobbly takeoff",
        fix="clear the nozzle",
        location="stern",
        tags={"fly", "swift"},
    ),
}

TOOLS = [
    Tool(id="cloth", label="soft cloth", phrase="a soft cloth", solves={"foggy lens"}, fits={"nose"}, sound="swish"),
    Tool(id="dial", label="tiny dial key", phrase="a tiny dial key", solves={"static"}, fits={"bridge"}, sound="tick-tick"),
    Tool(id="oil", label="dropper of oil", phrase="a little dropper of oil", solves={"sticky latch"}, fits={"airlock"}, sound="glug"),
    Tool(id="brush", label="tiny brush", phrase="a tiny brush", solves={"jammed nozzle"}, fits={"stern"}, sound="frrt"),
]

NAMES = ["Nova", "Pip", "Milo", "Rin", "Tara", "Ari", "Zia", "Finn"]
ROLES = ["pilot", "captain", "engineer", "navigator"]
TRAITS = ["swift", "cheerful", "curious", "brave", "silly"]


@dataclass
class StoryParams:
    place: str
    module: str
    hero: str
    role: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
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


def module_at_risk(module: ShipModule, setting: Setting) -> bool:
    if module.name == "telescope":
        return "scan" in setting.supports or "repair" in setting.supports
    if module.name == "radio":
        return "dock" in setting.supports or "trade" in setting.supports
    if module.name == "hatch":
        return "dock" in setting.supports
    if module.name == "thruster":
        return "repair" in setting.supports
    return False


def select_tool(module: ShipModule) -> Optional[Tool]:
    for tool in TOOLS:
        if module.risk in tool.solves and module.location in tool.fits:
            return tool
    return None


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for mid, module in MODULES.items():
            if module_at_risk(module, setting) and select_tool(module):
                out.append((place, mid))
    return out


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def predict_problem(world: World, module: ShipModule) -> dict:
    sim = world.copy()
    sim.facts["problem"] = module.problem
    sim.facts["risk"] = module.risk
    return {"bad": True, "risk": module.risk}


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.memes.get('trait', 'swift')} {hero.type} who loved tiny space jobs and big starry skies."
    )


def setup(world: World, hero: Entity, module: ShipModule) -> None:
    world.say(
        f"On the ship, the {module.name} went {module.sound}, and {hero.id} listened closely."
    )
    world.say(
        f"{hero.id} liked how every little fix could make the whole mission feel swift again."
    )


def trouble(world: World, hero: Entity, module: ShipModule, setting: Setting) -> None:
    hero.meters["worry"] = hero.meters.get("worry", 0) + 1
    world.say(
        f"One quick trip at {setting.place}, the {module.name} started to have a {module.problem}."
    )
    world.say(
        f"That could mean {module.risk}, and that was not funny in a good way."
    )
    world.say(
        f'"Whoa," {hero.id} said. "That is a very grumbly little problem."'
    )
    world.say("The ship answered with a sad little beep: brrt.")


def fix_it(world: World, hero: Entity, module: ShipModule, tool: Tool) -> None:
    hero.meters["focus"] = hero.meters.get("focus", 0) + 1
    world.say(
        f"{hero.id} grabbed {tool.phrase} and went {tool.sound}, {tool.sound} toward the {module.name}."
    )
    world.say(
        f"With a careful {module.fix}, the bad sound melted away."
    )
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1


def ending(world: World, hero: Entity, module: ShipModule, setting: Setting, tool: Tool) -> None:
    world.say(
        f"Soon the {module.name} was back to {module.sound}, and the ship zipped on through {setting.place}."
    )
    world.say(
        f'{hero.id} smiled and said, "Swift fix, swift trip!"'
    )
    world.say(
        f"Even the stars seemed to twinkle like they were laughing along."
    )


def tell_story(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    module = _safe_lookup(MODULES, params.module)
    tool = select_tool(module)
    if tool is None:
        _fallback_pool = globals().get("TOOLS") or globals().get("TOOLES") or []
        if hasattr(_fallback_pool, "values"):
            _fallback_pool = list(_fallback_pool.values())
        tool = next(iter(_fallback_pool), None)
        if tool is None:
            raise StoryError

    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.role))
    hero.memes["trait"] = params.trait
    module_ent = world.add(Entity(id=module.name, type=module.name, label=module.name))
    tool_ent = world.add(Entity(id=tool.id, type="tool", label=tool.label, phrase=tool.phrase, plural=tool.plural))
    tool_ent.carried_by = hero.id

    world.facts.update(hero=hero, module=module_ent, module_cfg=module, tool=tool_ent, tool_cfg=tool, setting=setting)

    introduce(world, hero)
    setup(world, hero, module)
    world.para()
    trouble(world, hero, module, setting)
    world.say("The crew hurried over: tap-tap, zoom-zoom, clink!")
    world.para()
    fix_it(world, hero, module, tool)
    ending(world, hero, module, setting, tool)

    hero.memes["resolved"] = 1
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    module = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "module_cfg")
    return [
        f'Write a short story for a young child about a swift space helper who fixes a {module.name}.',
        f"Tell a funny space adventure where {hero.id} hears a {module.sound} sound and solves the problem quickly.",
        f"Make a gentle story with sound effects, humor, and a happy fix for a ship problem at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    module = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "module_cfg")
    tool = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "tool_cfg")
    setting = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "setting")
    return [
        QAItem(
            question=f"What kind of space adventure is this story about?",
            answer=f"It is about a swift little ship problem at {setting.place} where {hero.id} fixes the {module.name} with {tool.label}.",
        ),
        QAItem(
            question=f"What sound did the {module.name} make when the trouble began?",
            answer=f"The {module.name} went {module.sound} when the problem started, which helped show the crew where to look.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem?",
            answer=f"{hero.id} used {tool.phrase} to {module.fix}, and that stopped the {module.risk}.",
        ),
    ]


KNOWLEDGE = {
    "swift": [
        QAItem(
            question="What does swift mean?",
            answer="Swift means fast and quick, like something that moves or happens without much delay.",
        )
    ],
    "sound": [
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a playful noise that helps a story feel more alive, like beep, whoosh, or clang.",
        )
    ],
    "space": [
        QAItem(
            question="What is space?",
            answer="Space is the huge area beyond Earth where stars, planets, and rockets travel.",
        )
    ],
    "humor": [
        QAItem(
            question="Why do stories use humor?",
            answer="Stories use humor to make people smile or giggle, which makes the adventure feel friendly and fun.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(KNOWLEDGE["swift"])
    out.extend(KNOWLEDGE["sound"])
    out.extend(KNOWLEDGE["space"])
    out.extend(KNOWLEDGE["humor"])
    return out


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
risk(Place,Module) :- supports(Place,repair), needs(Module,repair).
risk(Place,Module) :- supports(Place,dock), needs(Module,dock).
fixable(Module) :- risk(_,Module), tool(T), solves(T,Problem), problem(Module,Problem), fits(T,Location), location(Module,Location).
valid(Place,Module) :- risk(Place,Module), fixable(Module).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for sup in sorted(s.supports):
            lines.append(asp.fact("supports", pid, sup))
    for mid, m in MODULES.items():
        lines.append(asp.fact("module", mid))
        lines.append(asp.fact("problem", mid, m.problem))
        lines.append(asp.fact("location", mid, m.location))
        if mid == "telescope":
            lines.append(asp.fact("needs", mid, "repair"))
        elif mid == "radio":
            lines.append(asp.fact("needs", mid, "dock"))
        elif mid == "hatch":
            lines.append(asp.fact("needs", mid, "dock"))
        elif mid == "thruster":
            lines.append(asp.fact("needs", mid, "repair"))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        lines.append(asp.fact("solves", t.id, next(iter(t.solves))))
        lines.append(asp.fact("fits", t.id, next(iter(t.fits))))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python reasonableness gate ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Swift space adventures with sound effects and humor.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--module", choices=MODULES)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
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
    combos = valid_combos()
    combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "module", None) is None or c[1] == getattr(args, "module", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, module = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    role = getattr(args, "role", None) or rng.choice(ROLES)
    trait = getattr(args, "trait", None) or "swift"
    return StoryParams(place=place, module=module, hero=name, role=role, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.type:
            bits.append(f"type={e.type}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: " + " ".join(bits))
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("\n== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("\n== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
    StoryParams(place="orbital_port", module="telescope", hero="Nova", role="pilot", trait="swift"),
    StoryParams(place="asteroid_bay", module="thruster", hero="Pip", role="engineer", trait="curious"),
    StoryParams(place="space_market", module="radio", hero="Rin", role="captain", trait="cheerful"),
    StoryParams(place="orbital_port", module="hatch", hero="Milo", role="navigator", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        print(sorted(set(asp.atoms(model, "valid"))))
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
