#!/usr/bin/env python3
"""
A small space-adventure storyworld about a repeating problem on a ship.

Premise:
- A crew member named Jean is on a little starship with Batter and a Russian-speaking pilot.
- A repeating system glitch keeps a cabin door from staying shut.
- The crew must notice the pattern, fix the cause, and end with a calm ship.

The story model uses physical meters and emotional memes:
- meters: things like charge, pressure, frost, and repair state
- memes: worry, courage, relief, and frustration

The key narrative instrument is repetition:
- a problem returns in a similar form
- the hero tries again with a different method
- the repeated beat makes the turn and resolution feel earned
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


# ---------------------------------------------------------------------------
# Entities and world state
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
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    roles: set[str] = field(default_factory=set)
    language: str = "en"

    guest: object | None = None
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class StoryParams:
    ship: str
    hero: str
    helper: str
    guest: str
    glitch: str
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


@dataclass
class Setting:
    name: str
    detail: str
    repeat_place: str
    danger: str
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


@dataclass
class Problem:
    id: str
    label: str
    repeat_line: str
    physical: str
    emotional: str
    fix: str
    cause: str
    risk_meter: str
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
class Support:
    id: str
    label: str
    method: str
    tool: str
    protects: str
    calm_line: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "orbit_lab": Setting(
        name="orbit lab",
        detail="The little orbit lab floated above a blue planet with quiet windows and bright panels.",
        repeat_place="the same narrow corridor",
        danger="the air could slip away if the door stayed open",
    ),
    "moon_base": Setting(
        name="moon base",
        detail="The moon base sat under silver dust, with tunnels that hummed softly at night.",
        repeat_place="the same airlock",
        danger="the cold moon air could sneak into the base",
    ),
    "star_ship": Setting(
        name="star ship",
        detail="The star ship glided through dark space, its cabin lights blinking like tiny stars.",
        repeat_place="the same hatchway",
        danger="the ship could lose warmth and pressure",
    ),
}

PROBLEMS = {
    "door_glitch": Problem(
        id="door_glitch",
        label="door glitch",
        repeat_line="Again the door slid halfway, then shuddered and popped back open.",
        physical="half-open",
        emotional="frustrated",
        fix="reset the hinge sensor",
        cause="a tiny jam in the sensor track",
        risk_meter="open",
    ),
    "frost_patch": Problem(
        id="frost_patch",
        label="frost patch",
        repeat_line="Again a white frost patch spread across the panel and made it sticky.",
        physical="icy",
        emotional="worried",
        fix="warm the panel with a battery pad",
        cause="cold from the vent line",
        risk_meter="frost",
    ),
    "signal_echo": Problem(
        id="signal_echo",
        label="signal echo",
        repeat_line="Again the radio sang the same message twice in a row.",
        physical="echoing",
        emotional="uneasy",
        fix="tune the antenna to one clear channel",
        cause="two antennas were listening at once",
        risk_meter="noise",
    ),
}

SUPPORTS = {
    "battery_pad": Support(
        id="battery_pad",
        label="battery pad",
        method="press a warm battery pad against it",
        tool="battery pad",
        protects="frost",
        calm_line="The warmth made the frost melt into safe water beads.",
    ),
    "toolkit": Support(
        id="toolkit",
        label="small toolkit",
        method="open the panel with a small toolkit",
        tool="toolkit",
        protects="open",
        calm_line="The screws clicked into place, and the door stayed shut.",
    ),
    "tuner": Support(
        id="tuner",
        label="signal tuner",
        method="turn the signal tuner with careful fingers",
        tool="signal tuner",
        protects="noise",
        calm_line="The radio found one clean voice and stopped repeating itself.",
    ),
}

GUEST_LANG = {
    "russian": "ru",
    "english": "en",
}

GIRL_NAMES = ["Jean", "Mira", "Nina", "Lena", "Tara", "Ivy"]
BOY_NAMES = ["Batter", "Oren", "Maks", "Leo", "Jon", "Eli"]


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def meter(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def bump(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = meter(entity, key) + amount


def mem(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def bump_mem(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = mem(entity, key) + amount


def repeat_phrase(problem: Problem, attempt: int) -> str:
    if attempt == 1:
        return f"At first, {problem.label} made the ship feel stuck."
    if attempt == 2:
        return f"Then it happened again, just like before."
    return problem.repeat_line


def simulate_attempt(world: World, hero: Entity, problem: Problem, support: Support, narrate: bool = False) -> None:
    bump(hero, "attempts")
    bump_mem(hero, "determined")
    if problem.id == "door_glitch":
        if support.protects == "open":
            bump(hero, "fixed")
            if narrate:
                world.say(support.calm_line)
        else:
            bump(hero, "risk")
    elif problem.id == "frost_patch":
        if support.protects == "frost":
            bump(hero, "fixed")
            bump(hero, "warmth")
            if narrate:
                world.say(support.calm_line)
        else:
            bump(hero, "risk")
    elif problem.id == "signal_echo":
        if support.protects == "noise":
            bump(hero, "fixed")
            if narrate:
                world.say(support.calm_line)
        else:
            bump(hero, "risk")


def reasonableness(problem: Problem, support: Support) -> bool:
    return problem.risk_meter == support.protects


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type="girl", label=params.hero))
    helper = world.add(Entity(id=params.helper, kind="character", type="boy", label=params.helper))
    guest = world.add(Entity(
        id=params.guest,
        kind="character",
        type="boy",
        label=params.guest,
        language="ru",
        roles={"guest"},
    ))
    problem = _safe_lookup(PROBLEMS, params.glitch)
    support = SUPPORTS["battery_pad" if problem.id == "frost_patch" else "toolkit" if problem.id == "door_glitch" else "tuner"]

    world.facts.update(hero=hero, helper=helper, guest=guest, problem=problem, support=support)

    world.say(f"{hero.id} was on the {setting.name}, and {helper.id} and {guest.id} were there too.")
    world.say(setting.detail)
    world.say(f"{guest.id} spoke in Russian, and {hero.id} liked the bright sound of the words.")
    world.say(f"{helper.id} carried a {support.label}, because space work was easier when tools were ready.")

    world.para()
    bump_mem(hero, "curious")
    bump_mem(helper, "steady")
    bump_mem(guest, "hopeful")
    world.say(f"One quiet turn, the ship began to repeat a little trouble.")
    world.say(f"{problem.repeat_line}")
    bump_mem(hero, "worried")
    bump_mem(helper, "alert")
    bump(world.get(params.ship), problem.risk_meter, 1)

    world.say(f"{hero.id} watched it closely and said, 'That happened again.'")
    world.say(f"{helper.id} nodded. 'Let's try the same place, but a better way,' {helper.id} said.")

    world.para()
    simulate_attempt(world, hero, problem, support, narrate=True)
    if not mem(hero, "fixed"):
        world.say(f"The first try did not solve it, so {hero.id} tried again.")
        world.say(repeat_phrase(problem, 2))
        simulate_attempt(world, hero, problem, support, narrate=True)

    if mem(hero, "fixed"):
        bump_mem(hero, "relief")
        bump_mem(helper, "relief")
        bump_mem(guest, "relief")
        world.say(f"This time, the fix held.")
        world.say(f"{support.calm_line}")
        world.say(f"{hero.id} smiled at {guest.id}, and {guest.id} answered with a happy Russian thank-you.")
    else:
        world.say(f"The trouble stayed, so the crew kept working until they found the right answer.")

    world.para()
    if problem.id == "door_glitch":
        ending = f"The hatch stayed shut, the air stayed steady, and the ship felt safe again."
    elif problem.id == "frost_patch":
        ending = f"The panel stayed clear, the frost melted away, and warm light glowed in the base."
    else:
        ending = f"The radio spoke once, then once more, and at last the second voice was gone."
    world.say(ending)
    world.say(f"After the repeated scare, the little crew knew the same problem would not win again.")

    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "problem")
    return [
        f'Write a small space adventure where a crew faces a repeating "{p.label}" problem and keeps trying until it is fixed.',
        f"Tell a child-friendly story about {world.facts['hero'].id}, {world.facts['helper'].id}, and a Russian-speaking guest aboard a tiny ship.",
        f"Write a story with repetition in space, where the same trouble happens again and the crew uses a careful tool to solve it.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    guest = _safe_fact(world, world.facts, "guest")
    problem = _safe_fact(world, world.facts, "problem")
    support = _safe_fact(world, world.facts, "support")
    return [
        QAItem(
            question=f"Who noticed the repeating trouble first on the ship?",
            answer=f"{hero.id} noticed it first and told the others that the same trouble had happened again.",
        ),
        QAItem(
            question=f"What kept happening in the story?",
            answer=f"{problem.repeat_line} That repeating trouble was the main problem the crew had to solve.",
        ),
        QAItem(
            question=f"What did the crew use to fix the problem?",
            answer=f"They used a {support.label}, and the crew kept trying until the fix held.",
        ),
        QAItem(
            question=f"Who spoke Russian in the story?",
            answer=f"{guest.id} spoke Russian, and the other characters listened to the words carefully.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the ship safe again, because the repeated problem was finally fixed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a battery pad for in a spaceship?",
            answer="A battery pad can hold warmth and give it to a cold part of a ship or machine.",
        ),
        QAItem(
            question="What does repeating mean?",
            answer="Repeating means something happens again in the same way, or with a very similar pattern.",
        ),
        QAItem(
            question="Why do crews check the same problem more than once?",
            answer="Crews check again because a problem that repeats can still be hiding its real cause.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"{e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A problem is compatible with a support when the support protects the same risk meter.
compatible(P, S) :- problem(P), support(S), problem_risk(P, R), support_protects(S, R).

% A story is valid if the selected problem has a matching support.
valid_story(S) :- selected_problem(P), selected_support(S), compatible(P, S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("setting_name", sid, s.name))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("problem_risk", pid, p.risk_meter))
    for sid, s in SUPPORTS.items():
        lines.append(asp.fact("support", sid))
        lines.append(asp.fact("support_protects", sid, s.protects))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    python_pairs = {(p.id, s.id) for p in PROBLEMS.values() for s in SUPPORTS.values() if reasonableness(p, s)}
    asp_pairs = set(asp_valid_pairs())
    if python_pairs == asp_pairs:
        print(f"OK: ASP matches Python gate ({len(python_pairs)} pairs).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(python_pairs - asp_pairs))
    print("asp-only:", sorted(asp_pairs - python_pairs))
    return 1


# ---------------------------------------------------------------------------
# Parameter resolution and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld with repetition.")
    ap.add_argument("--ship", choices=["orbit_lab", "moon_base", "star_ship"])
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--guest")
    ap.add_argument("--glitch", choices=list(PROBLEMS))
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
    ship = getattr(args, "ship", None) or rng.choice(list(SETTINGS))
    glitch = getattr(args, "glitch", None) or rng.choice(list(PROBLEMS))
    hero = getattr(args, "hero", None) or rng.choice(GIRL_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(BOY_NAMES)
    guest = getattr(args, "guest", None) or "Ivana"
    if getattr(args, "hero", None) and getattr(args, "helper", None) and getattr(args, "hero", None) == getattr(args, "helper", None):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(ship=ship, hero=hero, helper=helper, guest=guest, glitch=glitch)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.ship), params)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(ship="star_ship", hero="Jean", helper="Batter", guest="Ivana", glitch="door_glitch"),
    StoryParams(ship="moon_base", hero="Jean", helper="Batter", guest="Ivana", glitch="frost_patch"),
    StoryParams(ship="orbit_lab", hero="Jean", helper="Batter", guest="Ivana", glitch="signal_echo"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} compatible problem/support pairs:")
        for p, s in pairs:
            print(f"  {p} -> {s}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
            header = f"### {p.ship} / {p.glitch} / {p.hero}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
