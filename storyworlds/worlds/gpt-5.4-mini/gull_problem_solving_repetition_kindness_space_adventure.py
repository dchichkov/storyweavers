#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gull_problem_solving_repetition_kindness_space_adventure.py
===========================================================================================

A small standalone story world for a space-adventure tale about a friendly gull,
a repeated problem, kind help, and a clever solution.

The premise is simple: a gull gets inside a little moon station and causes a
repeat annoyance by stealing shiny parts. A child astronaut uses patience,
repetition, and kindness to solve the problem without scaring the bird away.
The ending proves what changed: the gull has a safe perch, the station is tidy,
and the children have a better routine for the next time it returns.

This script follows the Storyweavers storyworld contract:
- typed entities with meters and memes
- a reasonableness gate plus inline ASP twin
- story-driven prose and grounded QA
- standalone stdlib implementation
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
SENSE_MIN = 2


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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    label: str
    scene: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Problem:
    id: str
    label: str
    action: str
    repeats: int
    risk: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Tool:
    id: str
    label: str
    use: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class HelpPlan:
    id: str
    label: str
    steps: list[str]
    kindness: int
    solve_power: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    traveler = world.entities.get("child")
    gull = world.entities.get("gull")
    if not traveler or not gull:
        return out
    if traveler.memes["patience"] < THRESHOLD:
        return out
    sig = ("repeat", gull.id)
    if sig in world.fired:
        return out
    if gull.meters["taking"] >= THRESHOLD:
        world.fired.add(sig)
        traveler.memes["determination"] += 1
        out.append("__repeat__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    gull = world.entities.get("gull")
    if not child or not gull:
        return out
    if child.memes["kindness"] < THRESHOLD:
        return out
    sig = ("kindness", gull.id)
    if sig in world.fired:
        return out
    if gull.meters["calmed"] >= THRESHOLD:
        world.fired.add(sig)
        child.memes["joy"] += 1
        gull.memes["trust"] += 1
        out.append("__kindness__")
    return out


CAUSAL_RULES = [Rule("repeat", "social", _r_repeat), Rule("kindness", "social", _r_kindness)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def problem_at_risk(problem: Problem) -> bool:
    return problem.repeats >= 1


def sensible_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.safe]


def choose_tool(problem: Problem) -> Tool:
    if problem.id == "glint":
        return TOOLS["snack"]
    return TOOLS["net"]


def reason_possible(problem: Problem, plan: HelpPlan) -> bool:
    return problem.repeats <= plan.solve_power


def _do_problem(world: World, problem: Problem, narrate: bool = True) -> None:
    child = world.get("child")
    gull = world.get("gull")
    child.meters["stress"] += 1
    gull.meters["taking"] += 1
    gull.meters["glee"] += 1
    propagate(world, narrate=narrate)


def predict(world: World, problem: Problem) -> dict:
    sim = world.copy()
    _do_problem(sim, problem, narrate=False)
    return {
        "taking": sim.get("gull").meters["taking"],
        "stress": sim.get("child").meters["stress"],
    }


def setup(world: World, child: Entity, companion: Entity, place: Place) -> None:
    child.memes["wonder"] += 1
    companion.memes["warmth"] += 1
    world.say(
        f"Far from Earth, {child.id} and {companion.id} floated through {place.label}. "
        f"{place.scene}"
    )
    world.say(
        f"{child.id} liked the quiet hum of the station and the way the stars shone like tiny lanterns."
    )


def first_problem(world: World, child: Entity, gull: Entity, problem: Problem) -> None:
    world.say(
        f"Then a {problem.label} came drifting by. A small gull slipped through the open hatch and pecked at the control shelf."
    )
    world.say(
        f"It loved to {problem.action}, and it did the same thing again and again."
    )


def warn(world: World, companion: Entity, child: Entity, problem: Problem) -> None:
    pred = predict(world, problem)
    companion.memes["care"] += 1
    world.facts["predicted_taking"] = pred["taking"]
    world.say(
        f'{companion.id} pointed at the shelf. "{child.id}, that gull is going to keep taking the shiny bolts if we do nothing," {companion.pronoun()} said.'
    )


def try_again(world: World, child: Entity, problem: Problem) -> None:
    child.memes["patience"] += 1
    world.say(
        f'{child.id} took a slow breath, then tried a second time. "{problem.risk}," {child.id} whispered, and waited for the gull to settle.'
    )


def kind_help(world: World, child: Entity, gull: Entity, plan: HelpPlan, tool: Tool) -> None:
    gull.meters["calmed"] += 1
    child.memes["kindness"] += 1
    world.say(
        f"Instead of chasing it, {child.id} used {tool.label} and {plan.label}."
    )
    world.say(
        f"{plan.steps[0].capitalize()}, then {plan.steps[1]}, then {plan.steps[2]}. The gull blinked, snatched the snack, and hopped to the side."
    )
    propagate(world, narrate=False)


def solve(world: World, child: Entity, gull: Entity, place: Place, plan: HelpPlan) -> None:
    child.memes["relief"] += 1
    gull.memes["trust"] += 1
    world.say(
        f"At last, the same problem had a better answer. {child.id} set a shiny perch by the window, and the gull chose it instead of the shelf."
    )
    world.say(
        f"The bolts stayed put, the hatch stayed closed, and the little station felt calm again."
    )
    world.say(
        f"Every time the gull returned, {child.id} used the same kind plan, and this time it worked."
    )


def tell(place: Place, problem: Problem, tool: Tool, plan: HelpPlan,
         child_name: str = "Mira", child_gender: str = "girl",
         companion_name: str = "Tavi", companion_gender: str = "boy") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="hero"))
    companion = world.add(Entity(id=companion_name, kind="character", type=companion_gender, role="helper"))
    gull = world.add(Entity(id="gull", kind="character", type="bird", role="mischief"))
    world.facts["place"] = place
    world.facts["problem"] = problem
    world.facts["tool"] = tool
    world.facts["plan"] = plan
    world.facts["child"] = child
    world.facts["companion"] = companion
    world.facts["gull"] = gull

    setup(world, child, companion, place)
    world.para()
    first_problem(world, child, gull, problem)
    warn(world, companion, child, problem)
    try_again(world, child, problem)
    _do_problem(world, problem, narrate=False)
    world.say(f"The gull did it again, because shiny things were hard to ignore.")

    world.para()
    kind_help(world, child, gull, plan, tool)
    solve(world, child, gull, place, plan)

    world.facts["outcome"] = "solved"
    world.facts["resolved"] = True
    return world


PLACES = {
    "orbital_bay": Place("orbital_bay", "the orbital bay", "The windows opened onto a round wash of stars, and the station lights blinked softly.", {"space", "station"}),
    "moon_dock": Place("moon_dock", "the moon dock", "A silver moon hung below the hull, and the dock creaked like a sleepy boat.", {"space", "moon"}),
}

PROBLEMS = {
    "bolts": Problem("bolts", "bolt-bothering gull", "peck at the loose bolts", 2, "Those bolts keep your panel safe.", {"gull", "repeat", "problem"}),
    "crumbs": Problem("crumbs", "crumb-stealing gull", "come back for crumbs", 2, "Those crumbs belong in the bag.", {"gull", "repeat", "problem"}),
}

TOOLS = {
    "net": Tool("net", "a soft net", "guide the gull without hurting it", True, {"tool"}),
    "snack": Tool("snack", "a tiny snack trail", "lead the gull gently", True, {"tool", "kindness"}),
    "laser": Tool("laser", "a laser pointer", "chase the gull away", False, {"tool"}),
}

PLANS = {
    "window": HelpPlan("window", "a window perch plan", ["place a perch by the glass", "leave a little snack on it", "wait patiently"], 2, 2, {"kindness", "problem"}),
    "repeat_path": HelpPlan("repeat_path", "the same calm plan", ["move the loose bolts away", "offer the snack trail again", "show the gull the perch"], 3, 3, {"repetition", "kindness", "problem"}),
}

GULL_NAMES = ["gull"]


@dataclass
@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    plan: str
    child_name: str = "Mira"
    child_gender: str = "girl"
    companion_name: str = "Tavi"
    companion_gender: str = "boy"
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for problem in PROBLEMS:
            for plan in PLANS:
                if problem_at_risk(PROBLEMS[problem]) and reason_possible(PROBLEMS[problem], PLANS[plan]):
                    combos.append((place, problem, plan))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: Problem = f["problem"]
    pl: Place = f["place"]
    return [
        f'Write a space-adventure story for a young child that includes the word "gull" and ends with a calm solution.',
        f"Tell a story where a gull keeps causing the same problem at {pl.label}, and a child solves it with kindness.",
        f"Write a story about repetition and problem solving in space, where the gull comes back more than once and the hero stays gentle.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    comp: Entity = f["companion"]
    problem: Problem = f["problem"]
    place: Place = f["place"]
    plan: HelpPlan = f["plan"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id}, {comp.id}, and a gull at {place.label}. {child.id} is the one who figures out the kind solution."
        ),
        QAItem(
            question="Why was the gull a problem more than once?",
            answer=f"The gull kept going back to the shiny bolts and pecking at them again and again. That repetition made the problem keep returning until someone solved it kindly."
        ),
        QAItem(
            question="How did the child solve the problem?",
            answer=f"{child.id} used {TOOLS['snack'].label} and {plan.label}. The same calm steps were used again, and the gull learned to stay by the window perch instead."
        ),
        QAItem(
            question="What changed at the end?",
            answer=f"The bolts stayed safe, the gull had a better place to land, and the station felt calm. The repeated problem turned into a routine that worked."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gull?",
            answer="A gull is a seabird with wings and a beak. Gulls can be curious and sometimes grab shiny things."
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means helping without being mean or rough. A kind person tries to make things better for everyone."
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means something happens again and again. Sometimes you repeat a step until a problem is solved."
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means noticing what is wrong and choosing a smart way to fix it. Often it takes patience and a few careful tries."
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("orbital_bay", "bolts", "snack", "window", "Mira", "girl", "Tavi", "boy"),
    StoryParams("moon_dock", "crumbs", "net", "repeat_path", "Nia", "girl", "Leo", "boy"),
]


def explain_rejection(problem: Problem, plan: HelpPlan) -> str:
    if problem.repeats > plan.solve_power:
        return "(No story: that plan is not strong enough for a repeating problem.)"
    return "(No story: this combination is not reasonable.)"


def outcome_of(params: StoryParams) -> str:
    return "solved"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("repeats", pid, p.repeats))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.safe:
            lines.append(asp.fact("safe", tid))
    for pid, p in PLANS.items():
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("solve_power", pid, p.solve_power))
        lines.append(asp.fact("kindness", pid, p.kindness))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, Pr, Pl) :- place(P), problem(Pr), plan(Pl), repeats(Pr, R), solve_power(Pl, S), R =< S.
sensible(T) :- tool(T), safe(T).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(t for (t,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP gate matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"FAILED: generation crashed: {exc}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world with a gull, repetition, kindness, and problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--child-name")
    ap.add_argument("--companion-name")
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
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.plan is None or c[2] == args.plan)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, plan = rng.choice(sorted(combos))
    tool = args.tool or choose_tool(PROBLEMS[problem]).id
    child_name = args.child_name or rng.choice(["Mira", "Nia", "Luna", "Kai"])
    companion_name = args.companion_name or rng.choice(["Tavi", "Leo", "Rin", "Omar"])
    return StoryParams(place, problem, tool, plan, child_name, "girl", companion_name, "boy")


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], PROBLEMS[params.problem], TOOLS[params.tool], PLANS[params.plan], params.child_name, params.child_gender, params.companion_name, params.companion_gender)
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
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible tools: {', '.join(asp_sensible())}")
        print(f"{len(asp_valid_combos())} compatible combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
