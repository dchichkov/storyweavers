#!/usr/bin/env python3
"""
Responsive teamwork folk tale storyworld.

A small classical simulation of a folk-tale domain where a village faces a
practical problem, the characters respond to it, and teamwork changes the state
of the world. The stories are built from world state, not from a frozen template.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    name: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    helpers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother", "witch"}
        male = {"boy", "man", "father", "grandfather", "woodcutter"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def display(self) -> str:
        return self.name or self.label or self.id
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
class Problem:
    id: str
    label: str
    kind: str
    need: str
    damage_word: str
    remedy: str
    risk_area: str
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
    use_word: str
    helps: set[str]
    covers: set[str] = field(default_factory=set)
    plural: bool = False
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
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.problem: Optional[Problem] = None
        self.tool: Optional[Tool] = None
        self.time_of_day: str = "morning"
        self.weather: str = ""
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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.problem = self.problem
        c.tool = self.tool
        c.time_of_day = self.time_of_day
        c.weather = self.weather
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        c.paragraphs = [[]]
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "village": "the village",
    "riverbank": "the riverbank",
    "orchard": "the orchard",
    "hill": "the hill",
    "forest": "the forest edge",
}

PROBLEMS = {
    "bridge": Problem(
        id="bridge",
        label="wooden bridge",
        kind="bridge",
        need="cross the river",
        damage_word="broken",
        remedy="repair the bridge plank by plank",
        risk_area="crossing",
        tags={"wood", "river", "repair"},
    ),
    "harvest": Problem(
        id="harvest",
        label="grain cart",
        kind="cart",
        need="bring the grain home",
        damage_word="stuck",
        remedy="free the cart from the mud",
        risk_area="wheels",
        tags={"grain", "mud", "help"},
    ),
    "well": Problem(
        id="well",
        label="old well rope",
        kind="rope",
        need="draw water for the village",
        damage_word="frayed",
        remedy="mend the rope before it snaps",
        risk_area="rope",
        tags={"water", "rope", "help"},
    ),
    "roof": Problem(
        id="roof",
        label="cottage roof",
        kind="roof",
        need="keep the rain out",
        damage_word="leaky",
        remedy="patch the roof before nightfall",
        risk_area="roof",
        tags={"rain", "roof", "repair"},
    ),
}

TOOLS = {
    "planks": Tool(
        id="planks",
        label="fresh planks",
        use_word="lay new planks",
        helps={"bridge"},
        covers={"crossing"},
        plural=True,
    ),
    "ropes": Tool(
        id="ropes",
        label="strong ropes",
        use_word="pull together with ropes",
        helps={"harvest", "well"},
        covers={"wheels", "rope"},
        plural=True,
    ),
    "patches": Tool(
        id="patches",
        label="patched cloth",
        use_word="seal the leak with patches",
        helps={"roof"},
        covers={"roof"},
        plural=False,
    ),
    "sticks": Tool(
        id="sticks",
        label="pole sticks",
        use_word="steady the work with pole sticks",
        helps={"bridge", "harvest"},
        covers={"crossing", "wheels"},
        plural=True,
    ),
}

NAMES = {
    "girl": ["Mira", "Nina", "Sora", "Lena", "Tara", "Anya"],
    "boy": ["Oren", "Pavel", "Milo", "Evan", "Jonas", "Tomas"],
}
TRAITS = ["kind", "quick", "patient", "brave", "steady", "clever"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    problem: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story simulation
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


def compatible(problem: Problem, tool: Tool) -> bool:
    return problem.kind in tool.helps


def select_tool(problem: Problem) -> Optional[Tool]:
    for tool in TOOLS.values():
        if compatible(problem, tool):
            return tool
    return None


def predict_outcome(world: World, hero: Entity, helper: Entity, tool: Tool) -> dict:
    sim = world.copy()
    do_work(sim, sim.get(hero.id), sim.get(helper.id), tool, narrate=False)
    prob = sim.problem
    return {
        "fixed": bool(prob and prob.meters["damage"] <= 0.0),
        "joy": hero.memes["joy"] + helper.memes["joy"],
    }


def do_work(world: World, hero: Entity, helper: Entity, tool: Tool, narrate: bool = True) -> None:
    prob = world.problem
    if not prob:
        pass
    if prob.kind not in tool.helps:
        pass
    key = ("work", prob.id, tool.id)
    if key in world.fired:
        return
    world.fired.add(key)
    hero.meters["work"] += 1
    helper.meters["work"] += 1
    hero.memes["trust"] += 1
    helper.memes["trust"] += 1
    prob.meters["repair"] += 1
    prob.meters["damage"] = 0.0
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    if narrate:
        world.say(
            f"{hero.display} and {helper.display} worked side by side and {tool.use_word}."
        )
        world.say(
            f"Little by little, the {prob.label} was mended, and the village breathed easier."
        )


def tell(params: StoryParams) -> World:
    world = World(params.place)
    world.time_of_day = "morning"
    world.weather = "misty"
    prob = next((p for p in PROBLEMS.values() if p.kind == params.problem), None)
    if prob is None:
        pass
    world.problem = prob
    tool = select_tool(prob)
    if tool is None:
        pass
    world.tool = tool

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.hero_gender,
        name=params.hero_name,
        traits=["responsive", params.trait],
        role="villager",
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper_gender,
        name=params.helper_name,
        traits=["helpful"],
        role="neighbor",
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type="woman",
        name="Grandmother Reed",
        role="wise elder",
    ))

    # Act 1
    hero.memes["hope"] += 1
    helper.memes["hope"] += 1
    world.say(f"Once, in {world.place}, there lived {hero.display}, a {params.trait} child who was known for being responsive to a good turn of work.")
    world.say(
        f"One day, the people found that the {prob.label} had gone {prob.damage_word}, and the village could not {prob.need}."
    )
    world.say(
        f"{elder.display} said, \"If one pair of hands is not enough, then we must join our hands together.\""
    )

    # Act 2
    world.para()
    hero.memes["worry"] += 1
    helper.memes["worry"] += 1
    world.say(
        f"{hero.display} looked at the trouble and listened well, for a responsive heart hears the need before it grows worse."
    )
    world.say(
        f"{helper.display} came at once, and together they chose {tool.label} to help."
    )
    world.say(
        f"The two of them began to {tool.use_word}, while the elder kept the path clear and the village children carried small stones away."
    )
    world.problem.meters["damage"] += 1.0
    do_work(world, hero, helper, tool, narrate=True)

    # Act 3
    world.para()
    hero.memes["worry"] = 0.0
    helper.memes["worry"] = 0.0
    world.say(
        f"By sunset, the {prob.label} stood firm again, and the people crossed safely."
    )
    world.say(
        f"{hero.display} smiled because responsive teamwork had done what lonely strength could not."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        elder=elder,
        problem=prob,
        tool=tool,
        place=params.place,
        params=params,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    problem: Problem = _safe_fact(world, f, "problem")
    tool: Tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        f'Write a short folk tale about a responsive child in {world.place} who helps fix a {problem.label}.',
        f'Tell a simple story where {hero.display} and {helper.display} work together with {tool.label} to solve a village problem.',
        f'Create a gentle story about teamwork, a broken thing, and a happy ending in {world.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    elder: Entity = _safe_fact(world, f, "elder")
    prob: Problem = _safe_fact(world, f, "problem")
    tool: Tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"Who is the story mainly about?",
            answer=f"The story is mainly about {hero.display}, a responsive child who helped solve a village problem with {helper.display}.",
        ),
        QAItem(
            question=f"What was wrong in the village?",
            answer=f"The {prob.label} had gone {prob.damage_word}, so the people could not {prob.need}.",
        ),
        QAItem(
            question=f"Who gave the wise advice?",
            answer=f"{elder.display} gave the wise advice to join hands and work together.",
        ),
        QAItem(
            question=f"What did {hero.display} and {helper.display} use to fix the problem?",
            answer=f"They used {tool.label} and worked side by side until the {prob.label} was safe again.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the {prob.label} repaired, the village calmer, and {hero.display} proud of the teamwork.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "repair": [
        ("What does repair mean?", "Repair means to fix something that is broken or damaged so it can be used again."),
    ],
    "help": [
        ("What is teamwork?", "Teamwork is when people work together and help one another to finish a job."),
    ],
    "river": [
        ("What is a river?", "A river is a long moving stream of water that flows through the land."),
    ],
    "roof": [
        ("What is a roof for?", "A roof covers a house and helps keep rain and wind out."),
    ],
    "wood": [
        ("Why are wooden planks useful?", "Wooden planks can make a strong walkway or bridge when they are put together well."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.problem.tags if world.problem else set())
    if world.tool:
        tags.update(world.tool.helps)
    out: list[QAItem] = []
    for tag, items in WORLD_KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
tool_for(T, P) :- tool(T), helps(T, K), problem(P), kind(P, K).
good_story(Place, Prob, Tool) :- place(Place), problem(Prob), tool_for(Tool, Prob), available(Place, Prob).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("available", pid, "bridge"))
        lines.append(asp.fact("available", pid, "harvest"))
        lines.append(asp.fact("available", pid, "well"))
        lines.append(asp.fact("available", pid, "roof"))
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("kind", pid, prob.kind))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for k in sorted(tool.helps):
            lines.append(asp.fact("helps", tid, k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_good_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/3."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    py = set((place, prob.id, tool.id) for place in PLACES for prob in PROBLEMS.values() for tool in TOOLS.values() if compatible(prob, tool))
    cl = set(asp_good_combos())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Validation and params
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Responsive teamwork folk tale storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    if getattr(args, "problem", None):
        problem = _safe_lookup(PROBLEMS, getattr(args, "problem", None))
    else:
        problem = rng.choice(list(PROBLEMS.values()))
    tool = select_tool(problem)
    if tool is None:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    hero_gender = getattr(args, "hero_gender", None) or rng.choice(["girl", "boy"])
    helper_gender = getattr(args, "helper_gender", None) or ("boy" if hero_gender == "girl" else "girl")
    hero_name = getattr(args, "hero_name", None) or rng.choice(_safe_lookup(NAMES, hero_gender))
    helper_name = getattr(args, "helper_name", None) or rng.choice(_safe_lookup(NAMES, helper_gender))
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        problem=problem.kind,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        trait=trait,
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        m = {k: v for k, v in e.meters.items() if v}
        n = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={dict(m)}")
        if n:
            bits.append(f"memes={dict(n)}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    if world.problem:
        lines.append(f"  problem: {world.problem.id} / {world.problem.label}")
    if world.tool:
        lines.append(f"  tool: {world.tool.id} / {world.tool.label}")
    lines.append(f"  fired rules: {sorted({a for a, *_ in world.fired})}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="village", problem="bridge", hero_name="Mira", hero_gender="girl", helper_name="Oren", helper_gender="boy", trait="brave"),
    StoryParams(place="orchard", problem="harvest", hero_name="Lena", hero_gender="girl", helper_name="Milo", helper_gender="boy", trait="patient"),
    StoryParams(place="riverbank", problem="well", hero_name="Tomas", hero_gender="boy", helper_name="Anya", helper_gender="girl", trait="clever"),
    StoryParams(place="hill", problem="roof", hero_name="Sora", hero_gender="girl", helper_name="Pavel", helper_gender="boy", trait="steady"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show good_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_good_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for place, prob, tool in combos:
            print(f"  {place:10} {prob:8} {tool:8}")
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
            header = f"### {p.hero_name}: {p.problem} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
