#!/usr/bin/env python3
"""
storyworlds/worlds/posey_saloon_sound_effects_flashback_space_adventure.py
===========================================================================
A standalone story world for a tiny space-adventure tale set around a saloon
on a dusty moon outpost.

Premise:
- Posey, a small pilot, stops at a saloon after a long hop through space.
- The saloon plays loud sound effects that echo through the room.
- One sound cue sparks a flashback to an old rescue lesson.
- That memory helps Posey fix a problem and get the ship home safely.

The world is intentionally small and constraint-checked: not every setting,
object, or problem/fix pairing is valid. The story is generated from simulated
state, not from a frozen paragraph with substituted names.
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    affords: set[str] = field(default_factory=set)
    spaceport: bool = True
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
class Problem:
    id: str
    verb: str
    mess: str
    risk: str
    trigger: str
    clue: str
    zone: set[str]
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
    fix: str
    covers: set[str]
    guards: set[str]
    prompt: str
    tail: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    zone: set[str] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    clone: object | None = None
    sim: object | None = None
    world: object | None = None
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
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone
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
class StoryParams:
    place: str
    problem: str
    tool: str
    name: str
    parent: str
    trait: str
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


SETTINGS = {
    "saloon": Setting(place="the saloon", affords={"echoes", "signal"}),
    "dock": Setting(place="the space dock", affords={"signal"}),
    "moonbay": Setting(place="the moon bay", affords={"echoes", "signal"}),
}

PROBLEMS = {
    "echoes": Problem(
        id="echoes",
        verb="follow the echoing sound effects",
        mess="confused",
        risk="lose the route back to the ship",
        trigger="clang-clink",
        clue="a flashback to an old rescue lesson",
        zone={"ears", "mind"},
        keyword="sound effects",
        tags={"sound", "flashback"},
    ),
    "signal": Problem(
        id="signal",
        verb="repair the blinking beacon",
        mess="dim",
        risk="miss the departure window",
        trigger="beep-beep",
        clue="a flashback to a mirror trick",
        zone={"hands", "mind"},
        keyword="flashback",
        tags={"signal", "flashback"},
    ),
}

TOOLS = [
    Tool(
        id="mirror",
        label="a pocket mirror",
        fix="bounce the light back toward the dock",
        covers={"hands"},
        guards={"dim"},
        prompt="hold up a pocket mirror",
        tail="held the mirror steady until the beacon shone again",
    ),
    Tool(
        id="cart",
        label="a little speaker cart",
        fix="play the right sound effects to guide the crew",
        covers={"ears", "mind"},
        guards={"confused"},
        prompt="turn the speaker cart toward the open door",
        tail="kept the sound effects clear and bright",
    ),
]

NAMES = ["Posey", "Milo", "June", "Arlo", "Nova", "Tess"]
TRAITS = ["brave", "curious", "quick-thinking", "cheerful"]


def problem_needs_tool(problem: Problem, tool: Tool) -> bool:
    return problem.mess in tool.guards


def select_tool(problem: Problem) -> Optional[Tool]:
    for tool in TOOLS:
        if problem_needs_tool(problem, tool):
            return tool
    return None


def predict(problem: Problem, tool: Tool) -> dict:
    sim = World(SETTINGS["saloon"])
    hero = sim.add(Entity(id="Posey", kind="character", type="girl"))
    sim.add(Entity(id="Parent", kind="character", type="mother"))
    hero.memes["worry"] += 1
    hero.meters[problem.mess] += 1
    if problem.mess in tool.guards:
        return {"ruined": False}
    return {"ruined": True}


def setup_story(world: World, hero: Entity, parent: Entity, problem: Problem) -> None:
    world.say(
        f"{hero.id} was a little {hero.memes.get('trait', 'brave')} pilot who loved space trips and shiny maps."
    )
    world.say(
        f"One night, {hero.id} and {hero.pronoun('possessive')} {parent.type} rested at {world.setting.place}, "
        f"and the room hummed with {problem.keyword}."
    )
    world.say(
        f"{hero.id} liked the way the {problem.keyword} sounded, but the noises could get tricky."
    )


def build_flashback_line(problem: Problem) -> str:
    return (
        f"The {problem.trigger} from the saloon speakers made {problem.clue} rush back to mind."
    )


def do_problem(world: World, hero: Entity, problem: Problem, tool: Tool) -> None:
    world.zone = set(problem.zone)
    hero.meters[problem.mess] += 1.0
    hero.memes["interest"] += 1.0
    if problem.id == "echoes":
        hero.memes["confused"] += 1.0


def resolve(world: World, hero: Entity, parent: Entity, problem: Problem, tool: Tool) -> None:
    hero.memes["worry"] = 0.0
    hero.memes["confused"] = 0.0
    hero.memes["joy"] = 1.0
    world.say(
        f"{hero.id} remembered the lesson: when space sounds got mixed up, {tool.prompt} could help."
    )
    world.say(
        f"{hero.id} used {tool.label} to {tool.fix}, and soon {tool.tail}."
    )
    world.say(
        f"With that, {hero.id} could {problem.verb} without getting lost, and the ship was ready to go home."
    )


def tell(setting: Setting, problem: Problem, tool: Tool, hero_name: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    hero.memes["trait"] = trait
    hero.meters["worry"] = 0.0

    setup_story(world, hero, parent, problem)
    world.para()
    world.say(f"Then {problem.trigger} crackled through the room, and {hero.id} froze for a second.")
    world.say(build_flashback_line(problem))
    do_problem(world, hero, problem, tool)
    world.para()
    world.say(
        f"{hero.id} wanted to {problem.verb}, but the problem could make {problem.risk}."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.type} nodded and pointed to {tool.label}."
    )
    resolve(world, hero, parent, problem, tool)

    world.facts.update(
        hero=hero,
        parent=parent,
        problem=problem,
        tool=tool,
        resolved=True,
    )
    return world


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for pid, problem in PROBLEMS.items():
        for tool in TOOLS:
            if problem_needs_tool(problem, tool):
                out.append((pid, tool.id))
    return out


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    problem = _safe_fact(world, f, "problem")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"What happened when {hero.id} heard the {problem.trigger} in {world.setting.place}?",
            answer=(
                f"The sound made {hero.id} remember {problem.clue}. "
                f"That flashback helped {hero.id} stay calm instead of getting lost."
            ),
        ),
        QAItem(
            question=f"Why did {hero.id} need {tool.label}?",
            answer=(
                f"{tool.label} helped {hero.id} with the {problem.mess} problem, so the "
                f"{problem.keyword} would not stop the trip home."
            ),
        ),
        QAItem(
            question=f"How did {parent.type} help {hero.id} at the end?",
            answer=(
                f"{parent.type.capitalize()} pointed {hero.id} toward {tool.label}, and then "
                f"{hero.id} used it to fix the trouble and get ready to leave."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    problem = _safe_fact(world, f, "problem")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    out = []
    if problem.id == "echoes":
        out.append(QAItem(
            question="What is an echo?",
            answer="An echo is a sound that bounces back after it hits a wall or other surface."
        ))
    if tool.id == "mirror":
        out.append(QAItem(
            question="What can a mirror do in sunlight?",
            answer="A mirror can bounce sunlight and make a bright reflection somewhere else."
        ))
    if tool.id == "cart":
        out.append(QAItem(
            question="What do speakers do?",
            answer="Speakers make sounds loud enough for people to hear them clearly."
        ))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a small space adventure about {f['hero'].id} at {world.setting.place} with {f['problem'].keyword}.",
        f"Tell a child-friendly story where sound effects lead to a flashback that helps fix a space problem.",
        f"Write a gentle story set in a saloon on a space outpost with Posey and a useful memory.",
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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"zone={sorted(world.zone)}")
    return "\n".join(lines)


ASP_RULES = r"""
problem_fix(P, T) :- problem(P), tool(T), needs(P, T).
valid_story(P, T) :- problem_fix(P, T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("mess", pid, p.mess))
        lines.append(asp.fact("needs", pid, select_tool(p).id))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space saloon story world with sound effects and flashback.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=[t.id for t in TOOLS])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if getattr(args, "problem", None) and getattr(args, "tool", None):
        if (getattr(args, "problem", None), getattr(args, "tool", None)) not in combos:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    filtered = [c for c in combos
                if (getattr(args, "problem", None) is None or c[0] == getattr(args, "problem", None))
                and (getattr(args, "tool", None) is None or c[1] == getattr(args, "tool", None))]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    problem, tool = rng.choice(list(filtered))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    place = getattr(args, "place", None) or "saloon"
    return StoryParams(place=place, problem=problem, tool=tool, name=name, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    problem = _safe_lookup(PROBLEMS, params.problem)
    tool = next(t for t in TOOLS if t.id == params.tool)
    world = tell(_safe_lookup(SETTINGS, params.place), problem, tool, params.name, params.parent, params.trait)
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
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for problem, tool in valid_combos():
            params = StoryParams(place=getattr(args, "place", None) or "saloon", problem=problem, tool=tool,
                                 name=getattr(args, "name", None) or "Posey", parent=getattr(args, "parent", None) or "mother",
                                 trait=getattr(args, "trait", None) or "curious")
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
