#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/precipitate_problem_solving_rhyme_bad_ending_superhero.py
=============================================================================================================

A standalone superhero story world with a tiny state machine, a science-flavored
problem involving a precipitate, rhyme-shaped narration beats, and a deliberately
bad ending.

The seed image behind this world:
- A young superhero hears a cry for help in the city.
- A strange chemical precipitate starts clogging the river pumps.
- The hero tries to solve the problem with a gadget and a clever plan.
- The plan goes wrong, the villain slips away, and the ending is unhappy.

The world model keeps two kinds of state:
- meters: physical quantities like clogging, damage, and gadget charge.
- memes: emotional/social quantities like courage, hope, panic, and pride.

This script follows the Storyweavers contract and includes an inline ASP twin
for the reasonableness gate.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    problem_ent: object | None = None
    sidekick: object | None = None
    tool_ent: object | None = None
    villain: object | None = None
    def __post_init__(self) -> None:
        for k in ["clog", "damage", "charge", "heat", "noise"]:
            self.meters.setdefault(k, 0.0)
        for k in ["courage", "hope", "panic", "pride", "worry", "greed", "relief"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero"}
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
    label: str
    verb: str
    gerund: str
    noun: str
    risk: str
    zone: str
    tags: set[str] = field(default_factory=set)
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
    prelude: str
    tail: str
    helps: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    risky_against: set[str] = field(default_factory=set)
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
class StoryParams:
    place: str
    problem: str
    tool: str
    hero_name: str
    hero_kind: str
    sidekick_name: str
    villain_name: str
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
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


SETTINGS = {
    "river": Setting(
        place="the bright river bridge",
        detail="Below the bridge, the water churned around the pump house.",
        affords={"precipitate", "splash"},
    ),
    "lab": Setting(
        place="the city lab",
        detail="Glass tubes clicked, and a silver drain ran under the floor.",
        affords={"precipitate"},
    ),
    "roof": Setting(
        place="the clock tower roof",
        detail="The wind tugged at banners and made every footstep sound sharp.",
        affords={"precipitate", "spark"},
    ),
}

PROBLEMS = {
    "precipitate": Problem(
        id="precipitate",
        label="a chalky precipitate",
        verb="clear the precipitate",
        gerund="clearing the precipitate",
        noun="precipitate",
        risk="it will clog the pumps",
        zone="pipes",
        tags={"science", "white", "clog"},
    ),
    "spark": Problem(
        id="spark",
        label="a sparking control box",
        verb="stop the sparks",
        gerund="stopping the sparks",
        noun="sparks",
        risk="the wires will snap",
        zone="wires",
        tags={"electric", "danger"},
    ),
}

TOOLS = {
    "filter": Tool(
        id="filter",
        label="a shiny filter wand",
        prelude="held up a shiny filter wand",
        tail="twirled the filter wand",
        helps={"precipitate"},
        covers={"pipes"},
        risky_against={"spark"},
    ),
    "shield": Tool(
        id="shield",
        label="a small shield disk",
        prelude="raised a small shield disk",
        tail="spun the shield disk",
        helps={"spark"},
        covers={"wires"},
        risky_against={"precipitate"},
    ),
}

HEROES = [
    ("Nova", "girl"),
    ("Blaze", "boy"),
    ("Comet", "girl"),
    ("Jet", "boy"),
]

SIDEKICKS = ["Pip", "Milo", "Tess", "Rae"]
VILLAINS = ["Dr. Brine", "Captain Crumble", "The Sable Smog"]


def hero_label(kind: str) -> str:
    return "heroine" if kind == "girl" else "hero"


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def setup_story(world: World, hero: Entity, sidekick: Entity, villain: Entity, problem: Problem, tool: Tool) -> None:
    hero.memes["courage"] += 1
    hero.memes["hope"] += 1
    sidekick.memes["worry"] += 1
    villain.memes["greed"] += 1

    world.say(
        f"{hero.id} was a small {hero_label(hero.type)} in a blue cape who watched over {world.setting.place}."
    )
    world.say(
        f"{sidekick.id} stayed near {hero.id} and said, "
        f"'{problem.verb.capitalize()} now, or the city will frown.'"
    )
    world.say(
        f"Up on the catwalk, {villain.id} stirred trouble with {tool.label} scraps and a mean little grin."
    )
    world.say(
        f"The trouble grew into {problem.label}; {problem.risk}."
    )


def predict_outcome(world: World, hero: Entity, problem: Problem, tool: Tool) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters["charge"] -= 1
    if problem.id in tool.helps:
        sim.get(problem.id).meters["clog"] = max(0.0, sim.get(problem.id).meters["clog"] - 1.0)
    else:
        sim.get(problem.id).meters["damage"] += 1
    return {
        "fixed": sim.get(problem.id).meters["clog"] < THRESHOLD,
        "worse": sim.get(problem.id).meters["damage"] >= THRESHOLD,
    }


def act_and_fail(world: World, hero: Entity, sidekick: Entity, villain: Entity, problem: Problem, tool: Tool) -> None:
    world.para()
    world.say(
        f"{hero.id} saw the mess, took a deep breath, and promised, "
        f"'I'll make it right tonight.'"
    )
    world.say(
        f"{hero.id} {tool.prelude}, but the city lights flashed and the wrong gears whirred."
    )
    hero.meters["charge"] += 1
    hero.meters["courage"] += 1
    world.say(
        f"{hero.id} tried to {problem.verb}, yet the tool was a poor match for the job."
    )

    if problem.id not in tool.helps:
        problem.meters["damage"] += 1
        hero.memes["panic"] += 1
        sidekick.memes["worry"] += 1
        world.say(
            f"The {problem.noun} only spread; {problem.risk}."
        )
        world.say(
            f"{sidekick.id} shouted, 'Oh no, that glow is a no-go!'"
        )
    else:
        problem.meters["clog"] += 1
        hero.memes["panic"] += 1
        world.say(
            f"The filter only scraped the top, and the chalky bits clumped harder."
        )
        world.say(
            f"'{tool.tail} slow!' cried {sidekick.id}, but the paste set like snow."
        )

    villain.memes["pride"] += 1
    villain.meters["noise"] += 1
    world.say(
        f"Then {villain.id} laughed, grabbed the last clean wrench, and vanished through the steam."
    )


def bad_ending(world: World, hero: Entity, sidekick: Entity, villain: Entity, problem: Problem) -> None:
    world.para()
    hero.memes["hope"] = 0.0
    hero.memes["pride"] = 0.0
    hero.memes["panic"] += 1
    sidekick.memes["hope"] = 0.0
    world.say(
        f"By morning, the bridge still sagged, the pipes were still stuck, and {hero.id}'s cape had a gray stain."
    )
    world.say(
        f"{villain.id} got away, {sidekick.id} looked sad, and {hero.id} stood very still while the city waited."
    )
    world.say(
        f"That was a bad ending: the hero had tried, but {problem.label} won the day."
    )


def tell(setting: Setting, problem: Problem, tool: Tool, hero_name: str, hero_type: str, sidekick_name: str, villain_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type="sidekick"))
    villain = world.add(Entity(id=villain_name, kind="character", type="villain"))
    problem_ent = world.add(Entity(id=problem.id, kind="thing", type="problem", label=problem.label))
    tool_ent = world.add(Entity(id=tool.id, kind="thing", type="tool", label=tool.label))

    problem_ent.meters["clog"] = 1.0
    world.facts.update(hero=hero, sidekick=sidekick, villain=villain, problem=problem, tool=tool)

    setup_story(world, hero, sidekick, villain, problem, tool)
    act_and_fail(world, hero, sidekick, villain, problem, tool)
    bad_ending(world, hero, sidekick, villain, problem)
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for prob_id in setting.affords:
            for tool_id, tool in TOOLS.items():
                if prob_id in tool.helps:
                    combos.append((place, prob_id, tool_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a young child that uses the word "precipitate" and ends badly.',
        f"Tell a short superhero tale where {f['hero'].id} tries to {f['problem'].verb} with {(f.get('tool') or next(iter(TOOLS.values()))).label}, but the plan fails.",
        f"Write a rhyming rescue story set at {world.setting.place} with a sad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    sidekick = _safe_fact(world, f, "sidekick")
    villain = _safe_fact(world, f, "villain")
    problem = _safe_fact(world, f, "problem")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"What problem did {hero.id} try to solve?",
            answer=f"{hero.id} tried to solve {problem.label}. The trouble was that {problem.risk}.",
        ),
        QAItem(
            question=f"What tool did {hero.id} use?",
            answer=f"{hero.id} used {tool.label}, but it was not the right fix for the whole mess.",
        ),
        QAItem(
            question=f"Who watched the rescue and worried?",
            answer=f"{sidekick.id} watched closely and worried when the plan went wrong.",
        ),
        QAItem(
            question=f"Why was the ending bad?",
            answer=(
                f"The ending was bad because the problem was not solved, {villain.id} got away, "
                f"and the city still had to wait."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a precipitate?",
            answer=(
                "A precipitate is a solid that forms out of a liquid, often making the liquid cloudy "
                "or leaving bits that can clog pipes."
            ),
        ),
        QAItem(
            question="What does a hero do?",
            answer="A hero tries to help people, solve danger, and keep a place safe.",
        ),
        QAItem(
            question="Why do people use a filter?",
            answer="People use a filter to catch bits they do not want, so the liquid can flow better.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==", ""]
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
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
problem(P) :- problem_id(P).
tool(T) :- tool_id(T).

compatible(Place, Prob, Tool) :- affords(Place, Prob), helps(Tool, Prob).
valid_story(Place, Prob, Tool) :- compatible(Place, Prob, Tool).

% The inline declarative twin of the Python gate:
% a setting must afford the problem, and the tool must actually help it.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for p in sorted(s.affords):
            lines.append(asp.fact("affords", pid, p))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem_id", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool_id", tid))
        for p in sorted(t.helps):
            lines.append(asp.fact("helps", tid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero story world with precipitate trouble and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
    ap.add_argument("--villain")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
              and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, prob_id, tool_id = rng.choice(list(combos))
    if getattr(args, "gender", None) is None:
        gender = rng.choice(["girl", "boy"])
    else:
        gender = getattr(args, "gender", None)
    hero_name = getattr(args, "name", None) or rng.choice([n for n, g in HEROES if g == gender])
    sidekick = getattr(args, "sidekick", None) or rng.choice(SIDEKICKS)
    villain = getattr(args, "villain", None) or rng.choice(VILLAINS)
    return StoryParams(
        place=place,
        problem=prob_id,
        tool=tool_id,
        hero_name=hero_name,
        hero_kind=gender,
        sidekick_name=sidekick,
        villain_name=villain,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(PROBLEMS, params.problem),
        _safe_lookup(TOOLS, params.tool),
        params.hero_name,
        params.hero_kind,
        params.sidekick_name,
        params.villain_name,
    )
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


CURATED = [
    StoryParams(
        place="river",
        problem="precipitate",
        tool="filter",
        hero_name="Nova",
        hero_kind="girl",
        sidekick_name="Pip",
        villain_name="Dr. Brine",
    ),
    StoryParams(
        place="lab",
        problem="precipitate",
        tool="filter",
        hero_name="Blaze",
        hero_kind="boy",
        sidekick_name="Milo",
        villain_name="Captain Crumble",
    ),
    StoryParams(
        place="roof",
        problem="spark",
        tool="shield",
        hero_name="Comet",
        hero_kind="girl",
        sidekick_name="Rae",
        villain_name="The Sable Smog",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, problem, tool) combos:\n")
        for place, prob, tool in combos:
            print(f"  {place:5} {prob:11} {tool}")
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
            header = f"### {p.hero_name}: {p.problem} at {p.place} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
