#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/chicken_ingenue_problem_solving_animal_story.py
===============================================================================

A standalone animal-story world about a bright young ingenue, a chicken, and a
small problem that gets solved by careful thinking.

The premise is simple: a childlike ingenue and a chicken face a tiny practical
trouble, then test a few ideas, choose the sensible one, and end with a changed
scene that proves the fix worked.

This world keeps the Storyweavers contract:
- typed entities with physical meters and emotional memes
- a state-driven narrative engine
- a Python reasonableness gate and inline ASP twin
- prompt, story-grounded QA, and world-knowledge QA generated from world state
- standard CLI flags including --verify and --show-asp
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen"}
        male = {"boy", "father", "dad", "man", "rooster"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Scene:
    id: str
    place: str
    trouble: str
    detail: str
    fix_word: str
    ending_image: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Problem:
    id: str
    label: str
    trigger: str
    risk: str
    clue: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Tool:
    id: str
    label: str
    kind: str
    safe: bool = True
    power: int = 1
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class World:
    scene: Scene
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.scene)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_confusion(world: World) -> list[str]:
    out: list[str] = []
    problem = world.facts.get("problem")
    chicken = world.facts.get("chicken")
    ingenue = world.facts.get("ingenue")
    if not problem or not chicken or not ingenue:
        return out
    if world.fired and ("confusion", problem.id) in world.fired:
        return out
    if chicken.meters["stuck"] >= THRESHOLD or problem.id == "gate":
        if ("confusion", problem.id) not in world.fired:
            world.fired.add(("confusion", problem.id))
            ingenue.memes["worry"] += 1
            chicken.memes["trouble"] += 1
            out.append("__confusion__")
    return out


def _r_solution(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("solution_used"):
        if ("solution", "done") not in world.fired:
            world.fired.add(("solution", "done"))
            chicken = world.facts["chicken"]
            ingenue = world.facts["ingenue"]
            chicken.meters["free"] = 1
            chicken.meters["stuck"] = 0
            ingenue.memes["pride"] += 1
            ingenue.memes["relief"] += 1
            out.append("__solution__")
    return out


CAUSAL_RULES = [
    Rule("confusion", "social", _r_confusion),
    Rule("solution", "physical", _r_solution),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_problem(problem: Problem) -> bool:
    return bool(problem.trigger and problem.risk)


def valid_tool(tool: Tool) -> bool:
    return tool.safe and tool.power >= 1


def can_use(tool: Tool, problem: Problem) -> bool:
    return tool.safe and problem.id in {"gate", "fence", "basket"} and tool.kind in {"rope", "stick", "key", "ladder"}


def solve_by(tool: Tool, problem: Problem) -> bool:
    return can_use(tool, problem)


def choose_scene(scene_id: str) -> Scene:
    if scene_id not in SCENES:
        raise StoryError("(No story: unknown scene.)")
    return SCENES[scene_id]


def _do_problem(world: World, problem: Problem, narrate: bool = True) -> None:
    world.get("chicken").meters["stuck"] = 1
    world.get("chicken").attrs["problem"] = problem.id
    propagate(world, narrate=narrate)


def intro(world: World, ingenue: Entity, chicken: Entity, scene: Scene) -> None:
    ingenue.memes["curiosity"] += 1
    chicken.memes["trust"] += 1
    world.say(
        f"In {scene.place}, an ingenue named {ingenue.id} found a chicken named {chicken.id}. "
        f"{scene.detail}"
    )
    world.say(
        f"{ingenue.id} was the sort of ingenue who noticed small troubles right away, and "
        f"{chicken.id} was the sort of chicken who pecked at everything twice."
    )


def trouble(world: World, ingenue: Entity, chicken: Entity, problem: Problem) -> None:
    ingenue.memes["attention"] += 1
    world.say(
        f"Then they saw the {problem.label}. {problem.clue} "
        f"The little problem made the path feel too narrow for {chicken.id}."
    )
    chicken.meters["stuck"] = 1
    _do_problem(world, problem, narrate=True)


def think(world: World, ingenue: Entity, chicken: Entity, tool: Tool) -> None:
    ingenue.memes["thinking"] += 1
    world.say(
        f'{ingenue.id} tilted {ingenue.pronoun("possessive")} head. "Let me think," '
        f'{ingenue.pronoun()} said. "{tool.label} might help if we use it the right way."'
    )
    chicken.memes["hope"] += 1


def test_options(world: World, ingenue: Entity, chicken: Entity, problem: Problem, alt_tool: Tool, main_tool: Tool) -> None:
    world.say(
        f"First, they tried the {alt_tool.label}. It looked clever, but it was too small to solve the {problem.label}."
    )
    ingenue.memes["patience"] += 1
    world.say(
        f"Then they checked the {main_tool.label}. That one fit the job much better."
    )
    world.facts["solution_used"] = True


def fix(world: World, ingenue: Entity, chicken: Entity, problem: Problem, tool: Tool) -> None:
    propagate(world, narrate=False)
    if not solve_by(tool, problem):
        raise StoryError("(No story: that tool cannot solve this problem.)")
    world.say(
        f"{ingenue.id} used the {tool.label} to open the {problem.label}. "
        f"With one careful move, the trouble gave way and {chicken.id} stepped free."
    )


def ending(world: World, scene: Scene, ingenue: Entity, chicken: Entity) -> None:
    ingenue.memes["joy"] += 1
    chicken.memes["joy"] += 1
    world.say(
        f"They looked back at the {scene.ending_image}, and now it seemed friendly instead of hard."
    )
    world.say(
        f"{chicken.id} clucked happily and {ingenue.id} laughed, because the day had turned from puzzling to bright."
    )


def tell(scene: Scene, problem: Problem, tools: tuple[Tool, Tool], seed_name: str, seed_chicken: str) -> World:
    world = World(scene=scene)
    ingenue = world.add(Entity(id=seed_name, kind="character", type="girl", role="ingenue", traits=["bright", "gentle"]))
    chicken = world.add(Entity(id=seed_chicken, kind="character", type="chicken", role="friend", traits=["busy", "feathery"]))
    world.facts["ingenue"] = ingenue
    world.facts["chicken"] = chicken
    world.facts["problem"] = problem
    world.facts["tools"] = tools

    intro(world, ingenue, chicken, scene)
    world.para()
    trouble(world, ingenue, chicken, problem)
    world.para()
    think(world, ingenue, chicken, tools[1])
    test_options(world, ingenue, chicken, problem, tools[0], tools[1])
    world.para()
    fix(world, ingenue, chicken, problem, tools[1])
    ending(world, scene, ingenue, chicken)

    world.facts.update(
        solved=True,
        tool=tools[1],
        alt_tool=tools[0],
        outcome="solved",
    )
    return world


SCENES = {
    "yard": Scene(
        id="yard",
        place="the sunny yard",
        trouble="a little stuck place",
        detail="A low wooden gate leaned shut, and the grass made a green path around it.",
        fix_word="open",
        ending_image="the gate standing open beside the grass path",
        tags={"yard", "gate"},
    ),
    "coop": Scene(
        id="coop",
        place="the chicken coop",
        trouble="a tight latch",
        detail="A tin latch had slipped down, and the coop door would not swing free.",
        fix_word="lift",
        ending_image="the coop door hanging open with fresh straw at the threshold",
        tags={"coop", "latch"},
    ),
    "orchard": Scene(
        id="orchard",
        place="the orchard",
        trouble="a bent basket handle",
        detail="A berry basket had snagged on a branch, and it tugged like it was asking for help.",
        fix_word="free",
        ending_image="the basket resting safely in the sun",
        tags={"orchard", "basket"},
    ),
}

PROBLEMS = {
    "gate": Problem(
        id="gate",
        label="gate",
        trigger="the gate would not open",
        risk="the chicken could not get through",
        clue="It had swung shut and stuck on a crooked peg.",
        tags={"gate"},
    ),
    "latch": Problem(
        id="latch",
        label="latch",
        trigger="the coop latch was jammed",
        risk="the chicken needed to go in and out",
        clue="It clicked, but it would not lift all the way.",
        tags={"latch"},
    ),
    "basket": Problem(
        id="basket",
        label="basket",
        trigger="the basket was caught",
        risk="the chicken kept pulling at the handle",
        clue="One side had hooked onto a twig and would not come loose.",
        tags={"basket"},
    ),
}

TOOLS = {
    "twig": Tool(id="twig", label="a twig", kind="stick", safe=True, power=1, tags={"stick"}),
    "rope": Tool(id="rope", label="a short rope", kind="rope", safe=True, power=2, tags={"rope"}),
    "key": Tool(id="key", label="a little key", kind="key", safe=True, power=2, tags={"key"}),
    "ladder": Tool(id="ladder", label="a small ladder", kind="ladder", safe=True, power=3, tags={"ladder"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava", "Elsie", "June", "Ruby", "Ivy"]
CHICKEN_NAMES = ["chicken", "Henrietta", "Penny", "Cluck", "Peep", "Sunny"]


@dataclass
class StoryParams:
    scene: str
    problem: str
    tool1: str
    tool2: str
    ingenue_name: str = "Mia"
    chicken_name: str = "chicken"
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for scene_id, scene in SCENES.items():
        for prob_id, prob in PROBLEMS.items():
            if not valid_problem(prob):
                continue
            if prob_id == "gate":
                for t1 in TOOLS:
                    for t2 in TOOLS:
                        if t1 != t2:
                            combos.append((scene_id, prob_id, t1))
            else:
                for t1 in TOOLS:
                    combos.append((scene_id, prob_id, t1))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene = f["problem"].label
    return [
        f'Write an animal story that includes the words "chicken" and "ingenue" and centers on a small problem in {f["scene"].place}.',
        f'Tell a gentle story where an ingenue and a chicken solve a {scene} problem by thinking carefully and choosing the right tool.',
        f'Write a child-friendly story about a chicken and an ingenue who try one idea, then solve the trouble with a better one.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    ingenue = f["ingenue"]
    chicken = f["chicken"]
    problem = f["problem"]
    tool = f["tool"]
    alt = f["alt_tool"]
    return [
        ("Who is in the story?",
         f"It is about {ingenue.id}, an ingenue, and {chicken.id}, a chicken. They face a small problem and solve it together."),
        ("What was the trouble?",
         f"The {problem.label} was stuck, so the chicken could not move the way it wanted to. That made the scene feel tight until they found a fix."),
        ("How did they solve it?",
         f"They tried a smaller idea first, then used {tool.label} because it fit the job better. That careful choice opened the way and let the chicken step free."),
        ("Why did the first idea not work?",
         f"{alt.label} was not enough for the job. It was a sensible guess, but the real trouble needed a stronger tool."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is an ingenue?",
         "An ingenue is a young, innocent character who is fresh and hopeful. In stories, an ingenue often notices a problem and tries to do the right thing."),
        ("What do chickens do?",
         "Chickens peck, cluck, scratch the ground, and look for seeds or bugs. They also like places where they can move around safely."),
        ("Why is it helpful to think before solving a problem?",
         "Thinking first helps you choose a tool that really fits the trouble. A careful choice works better than a random guess."),
        ("What happens when a door or gate is stuck?",
         "A stuck door or gate does not move the way it should. Often, a simple tool or a careful push can help it open again."),
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(scene="yard", problem="gate", tool1="twig", tool2="rope", ingenue_name="Mia", chicken_name="chicken"),
    StoryParams(scene="coop", problem="latch", tool1="key", tool2="ladder", ingenue_name="Lily", chicken_name="Henrietta"),
    StoryParams(scene="orchard", problem="basket", tool1="twig", tool2="rope", ingenue_name="Nora", chicken_name="Penny"),
]


def explain_rejection(problem: Problem, tool: Tool) -> str:
    if not solve_by(tool, problem):
        return f"(No story: {tool.label} cannot solve the {problem.label} problem.)"
    return "(No story: invalid combination.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: a chicken and an ingenue solve a tiny problem."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool1", choices=TOOLS)
    ap.add_argument("--tool2", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--chicken")
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
    if args.tool1 and args.problem and not solve_by(TOOLS[args.tool1], PROBLEMS[args.problem]):
        raise StoryError(explain_rejection(PROBLEMS[args.problem], TOOLS[args.tool1]))
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.problem is None or c[1] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, problem, tool1 = rng.choice(sorted(combos))
    tool2 = args.tool2 or rng.choice([t for t in TOOLS if t != tool1])
    if tool2 == tool1:
        tool2 = rng.choice([t for t in TOOLS if t != tool1])
    name = args.name or rng.choice(GIRL_NAMES)
    chicken = args.chicken or rng.choice(CHICKEN_NAMES)
    return StoryParams(scene=scene, problem=problem, tool1=tool1, tool2=tool2, ingenue_name=name, chicken_name=chicken)


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES or params.problem not in PROBLEMS or params.tool1 not in TOOLS or params.tool2 not in TOOLS:
        raise StoryError("(No story: invalid parameters.)")
    if params.tool1 == params.tool2:
        raise StoryError("(No story: the two tools should be different.)")
    scene = SCENES[params.scene]
    problem = PROBLEMS[params.problem]
    tools = (TOOLS[params.tool1], TOOLS[params.tool2])
    if not solve_by(tools[1], problem):
        raise StoryError(explain_rejection(problem, tools[1]))
    world = tell(scene, problem, tools, params.ingenue_name, params.chicken_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


ASP_RULES = r"""
valid(Scene, Problem, Tool1, Tool2) :- scene(Scene), problem(Problem), tool(Tool1), tool(Tool2), Tool1 != Tool2.
solves(Tool, Problem) :- tool(Tool), safe(Tool), problem(Problem), compatible(Tool, Problem).
good(Scene, Problem, Tool1, Tool2) :- valid(Scene, Problem, Tool1, Tool2), solves(Tool2, Problem).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.safe:
            lines.append(asp.fact("safe", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tag))
    for pid, p in PROBLEMS.items():
        for tid, t in TOOLS.items():
            if solve_by(t, p):
                lines.append(asp.fact("compatible", tid, pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good/4."))
    return sorted(set(asp.atoms(model, "good")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: normal generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"MISMATCH in smoke test: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show good/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible stories")
        for item in asp_valid_combos():
            print(item)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.ingenue_name} and {p.chicken_name}: {p.scene} / {p.problem}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
