#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/chimpanzee_orca_dialogue_problem_solving_cautionary_superhero.py
===============================================================================================

A small superhero-style storyworld about a chimpanzee hero, an orca helper, a
careful warning, and a problem solved by talking first and acting safely.

The seed words suggest a chimpanzee and an orca, so the world centers those
two characters. The stories are child-facing, action-forward, and cautionary:
the chimpanzee wants to rush in, the orca warns about a danger, they talk it
through, and they solve the problem together without making the mistake worse.

This script follows the storyworld contract:
- standalone stdlib script
- eager import of storyworlds/results.py containers
- lazy import of storyworlds/asp.py in ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support for default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    ally: object | None = None
    hero: object | None = None
    problem: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"chimpanzee", "chimp", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"orca", "whale", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
    place: str
    detail: str
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
class Problem:
    id: str
    verb: str
    noun: str
    danger: str
    caution: str
    fix_hint: str
    tag: str
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
class Tool:
    id: str
    label: str
    use_line: str
    safe_line: str
    fixes: set[str] = field(default_factory=set)
    supports: set[str] = field(default_factory=set)
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

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    hero_name: str
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


SETTINGS = {
    "harbor": Setting(
        place="the harbor",
        detail="The docks were slick, the water was dark, and gulls called over the boats.",
        affords={"drift", "storm", "tide"},
    ),
    "reef": Setting(
        place="the reef",
        detail="The coral shimmered under clear water, and the waves rolled softly.",
        affords={"tide", "drift"},
    ),
    "city": Setting(
        place="the waterfront city",
        detail="Tall buildings watched the bay, and a long pier stretched into the water.",
        affords={"drift", "storm"},
    ),
}

PROBLEMS = {
    "drifting_boat": Problem(
        id="drifting_boat",
        verb="drift toward the rocks",
        noun="a little boat",
        danger="the rocks",
        caution="the dock was slippery, and rushing could cause a fall",
        fix_hint="slow the boat first and keep everyone on steady ground",
        tag="boat",
    ),
    "stuck_buoy": Problem(
        id="stuck_buoy",
        verb="stay twisted on a line",
        noun="a bright buoy",
        danger="the buoy would keep signaling the wrong spot",
        caution="the line was tangled, and tugging too hard could snap it",
        fix_hint="untwist the line gently and check it twice",
        tag="buoy",
    ),
    "storm_lantern": Problem(
        id="storm_lantern",
        verb="go dark in the wind",
        noun="a signal lantern",
        danger="the harbor workers would lose their light",
        caution="the ladder swayed, and climbing in a hurry was risky",
        fix_hint="protect the lantern and carry it carefully",
        tag="lantern",
    ),
}

TOOLS = {
    "rope": Tool(
        id="rope",
        label="a strong rope",
        use_line="He could loop the rope around the post and pull slowly.",
        safe_line="The rope let them work without rushing into the water.",
        fixes={"drifting_boat", "storm_lantern"},
        supports={"harbor", "city"},
    ),
    "flashlight": Tool(
        id="flashlight",
        label="a bright flashlight",
        use_line="She could shine the light on the knot and find the twist.",
        safe_line="The flashlight helped them see every step before they moved.",
        fixes={"stuck_buoy", "storm_lantern"},
        supports={"harbor", "reef", "city"},
    ),
    "net_hook": Tool(
        id="net_hook",
        label="a long net hook",
        use_line="He could reach out with the hook and lift the line free.",
        safe_line="The hook kept their paws and fins away from the sharp parts.",
        fixes={"stuck_buoy", "drifting_boat"},
        supports={"harbor", "reef"},
    ),
}

HERO_TRAITS = ["brave", "curious", "quick", "steady", "kind", "bold"]
HERO_NAMES = ["Milo", "Niko", "Tara", "Luna", "Pip", "Ruby"]


def compatible_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for pid, prob in PROBLEMS.items():
            if prob.tag not in setting.affords:
                continue
            for tid, tool in TOOLS.items():
                if pid in tool.fixes and place in tool.supports:
                    out.append((place, pid, tid))
    return out


def reason_rejection(problem: Problem, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not safely solve {problem.noun}. "
        f"The cautionary superhero story needs a tool that truly fits the danger.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero storyworld about a chimpanzee, an orca, and careful problem solving."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=HERO_TRAITS)
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
    combos = [c for c in compatible_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if getattr(args, "problem", None) and getattr(args, "tool", None):
        prob, tool = _safe_lookup(PROBLEMS, getattr(args, "problem", None)), _safe_lookup(TOOLS, getattr(args, "tool", None))
        if getattr(args, "problem", None) not in tool.fixes:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, problem, tool = rng.choice(list(combos))
    return StoryParams(
        place=place,
        problem=problem,
        tool=tool,
        hero_name=getattr(args, "name", None) or rng.choice(HERO_NAMES),
        hero_trait=getattr(args, "trait", None) or rng.choice(HERO_TRAITS),
    )


def _setup_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type="chimpanzee",
        traits=["superhero", params.hero_trait],
        meters={"courage": 1.0},
        memes={"hope": 1.0},
    ))
    ally = world.add(Entity(
        id="Orca",
        kind="character",
        type="orca",
        label="the orca",
        traits=["superhero", "careful"],
        meters={"swim": 1.0},
        memes={"calm": 1.0},
    ))
    problem = world.add(Entity(
        id=params.problem,
        type="problem",
        label=_safe_lookup(PROBLEMS, params.problem).noun,
        phrase=_safe_lookup(PROBLEMS, params.problem).noun,
        owner=None,
        caretaker=None,
        meters={"danger": 1.0},
    ))
    tool = world.add(Entity(
        id=params.tool,
        type="tool",
        label=_safe_lookup(TOOLS, params.tool).label,
        phrase=_safe_lookup(TOOLS, params.tool).label,
        owner=hero.id,
        caretaker=hero.id,
        meters={"help": 1.0},
    ))
    world.facts.update(hero=hero, ally=ally, problem=problem, tool=tool, params=params)
    return world


def predict_outcome(world: World, params: StoryParams) -> dict:
    prob = _safe_lookup(PROBLEMS, params.problem)
    tool = _safe_lookup(TOOLS, params.tool)
    safe = params.problem in tool.fixes
    caution = prob.caution
    return {"safe": safe, "caution": caution}


def tell(world: World, params: StoryParams) -> World:
    hero = _safe_fact(world, world.facts, "hero")
    ally = _safe_fact(world, world.facts, "ally")
    prob = _safe_fact(world, world.facts, "problem")
    tool = _safe_fact(world, world.facts, "tool")
    p = _safe_lookup(PROBLEMS, params.problem)
    t = _safe_lookup(TOOLS, params.tool)
    setting = world.setting

    world.say(
        f"{hero.id} was a little {params.hero_trait} chimpanzee superhero who watched over {setting.place}."
    )
    world.say(
        f"Near the water, {ally.type} and {hero.id} spotted {prob.label}, and the problem made both heroes stop."
    )
    world.para()
    world.say(
        f'"{prob.label.capitalize()} is in trouble," {hero.id} said. "{p.verb.capitalize()} could get dangerous."'
    )
    world.say(
        f'"Yes," said the orca. "{p.caution.capitalize()}. Let us solve it carefully."'
    )
    world.para()
    world.say(
        f"{hero.id} nodded and picked up {t.label}. {t.use_line}"
    )
    world.say(
        f'The orca swam close and said, "{t.safe_line}"'
    )
    world.say(
        f"Together they fixed the problem, and {prob.label} stopped the danger before anything got hurt."
    )
    world.para()
    world.say(
        f"{hero.id} smiled. \"Superheroes can be fast,\" {hero.id} said, \"but careful is better.\""
    )
    world.say(
        f'The orca laughed softly. "A warning can save the day," she said, and the harbor looked calm again.'
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    prob = _safe_lookup(PROBLEMS, p.problem)
    return [
        f"Write a short superhero story for a child about a chimpanzee and an orca solving {prob.noun} with a warning first.",
        f"Tell a gentle dialogue-driven story where {p.hero_name} the chimpanzee listens to an orca and solves a danger at {_safe_lookup(SETTINGS, p.place).place}.",
        f"Write a cautionary superhero tale with talking heroes, careful choices, and a safe fix for {prob.noun}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    prob = _safe_lookup(PROBLEMS, p.problem)
    t = _safe_lookup(TOOLS, p.tool)
    hero = _safe_fact(world, world.facts, "hero")
    return [
        QAItem(
            question=f"Who are the two heroes in the story?",
            answer=f"The story is about {hero.id}, a chimpanzee superhero, and an orca who help each other."
        ),
        QAItem(
            question=f"What problem did they have to solve at {_safe_lookup(SETTINGS, p.place).place}?",
            answer=f"They had to solve {prob.noun} before {prob.danger} became a bigger problem."
        ),
        QAItem(
            question=f"What did the orca warn about before they acted?",
            answer=f"The orca warned that {prob.caution}."
        ),
        QAItem(
            question=f"How did they solve the problem safely?",
            answer=f"They used {t.label} and worked together instead of rushing in."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a superhero story?",
            answer="A superhero story is a tale about heroes who use courage, teamwork, and special skills to help others."
        ),
        QAItem(
            question="Why is a warning helpful?",
            answer="A warning is helpful because it can stop someone from making a dangerous mistake."
        ),
        QAItem(
            question="Why do problem solvers work together?",
            answer="Problem solvers work together because one helper may see a danger that another helper misses."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
compatible(Place,Problem,Tool) :- setting(Place), problem(Problem), tool(Tool),
                                  affords(Place,Tag), tags(Problem,Tag),
                                  fixes(Tool,Problem), supports(Tool,Place).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for tag in sorted(s.affords):
            lines.append(asp.fact("affords", pid, tag))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("tags", pid, p.tag))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for pr in sorted(t.fixes):
            lines.append(asp.fact("fixes", tid, pr))
        for pl in sorted(t.supports):
            lines.append(asp.fact("supports", tid, pl))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(compatible_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches compatible_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = _setup_world(params)
    tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


CURATED = [
    StoryParams(place="harbor", problem="drifting_boat", tool="rope", hero_name="Milo", hero_trait="brave"),
    StoryParams(place="reef", problem="stuck_buoy", tool="flashlight", hero_name="Tara", hero_trait="steady"),
    StoryParams(place="city", problem="storm_lantern", tool="rope", hero_name="Niko", hero_trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combinations:\n")
        for c in combos:
            print("  ", c)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
