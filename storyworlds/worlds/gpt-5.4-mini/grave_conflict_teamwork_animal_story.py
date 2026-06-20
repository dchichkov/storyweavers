#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/grave_conflict_teamwork_animal_story.py
=======================================================================

A standalone storyworld for a small animal tale built from the seed words
"grave", "Conflict", and "Teamwork" in an Animal Story style.

Premise:
- A pair of young animals visit a grave to leave flowers.
- A disagreement starts when they want to do the tribute differently.
- They learn to cooperate, combine their ideas, and make the grave look cared for.
- The ending shows a concrete change in the world: the grave is tidy, decorated,
  and the animals are calmer and kinder to each other.

This script follows the shared Storyweavers contract:
- stdlib only
- imports storyworlds/results.py eagerly
- lazy ASP import inside helper functions
- StoryParams, build_parser, resolve_params, generate, emit, main
- support default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, --show-asp
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
    owner: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    animals: list[str]


@dataclass
class Goal:
    id: str
    label: str
    verb: str
    help_phrase: str
    carries: str
    makes: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    tension: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    label: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_fear(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.meters["scared"] >= THRESHOLD and ("fear", e.id) not in world.fired:
            world.fired.add(("fear", e.id))
            e.memes["fear"] += 1
            out.append("")
    return out


def _r_calm(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.memes["shared_plan"] >= THRESHOLD and ("calm", e.id) not in world.fired:
            world.fired.add(("calm", e.id))
            e.memes["calm"] += 1
            out.append("")
    return out


CAUSAL_RULES = [Rule("fear", "social", _r_fear), Rule("calm", "social", _r_calm)]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world):
                changed = True


def reasonableness_gate(problem: Problem, goal: Goal, solution: Solution) -> bool:
    return problem.id == "grave_dirt" and goal.id == "flowers" and solution.sense >= 2


def sensible_solutions() -> list[Solution]:
    return [s for s in SOLUTIONS.values() if s.sense >= 2]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for goal in GOALS:
            for problem in PROBLEMS:
                for sol in sensible_solutions():
                    if reasonableness_gate(PROBLEMS[problem], GOALS[goal], sol):
                        combos.append((setting, goal, problem))
    return combos


def _do_problem(world: World, grave: Entity, problem: Problem) -> None:
    grave.meters["mess"] += 1
    grave.meters["dirt"] += 1
    world.get("animals").memes["worry"] += 1


def predict_solution(world: World, grave: Entity, problem: Problem, solution: Solution) -> dict:
    sim = world.copy()
    _do_problem(sim, sim.get("grave"), problem)
    apply_solution(sim, sim.get("grave"), solution, narrate=False)
    return {"clean": sim.get("grave").meters["clean"] >= THRESHOLD}


def apply_solution(world: World, grave: Entity, solution: Solution, narrate: bool = True) -> None:
    grave.meters["clean"] += solution.power
    if narrate:
        world.say(solution.text.replace("{grave}", grave.label_word))


def setup(world: World, setting: Setting, a: Entity, b: Entity, goal: Goal) -> None:
    world.say(
        f"On a quiet morning in {setting.place}, {a.id} and {b.id} padded along the path toward the old grave. "
        f"The {setting.mood} air made their little whiskers twitch."
    )
    world.say(
        f"They had brought {goal.carries}, because they wanted to {goal.verb} and make the place feel loved again."
    )


def conflict(world: World, a: Entity, b: Entity, goal: Goal, problem: Problem) -> None:
    a.memes["frustration"] += 1
    b.memes["frustration"] += 1
    world.say(
        f"But when they reached the grave, they started to disagree. {a.id} wanted to {goal.verb} one way, "
        f"and {b.id} thought a different way would be better."
    )
    world.say(
        f'The little argument grew sharp. "{a.id}, that will make {problem.risk}," {b.id} said, '
        f'and both animals stomped their paws.'
    )


def teamwork(world: World, a: Entity, b: Entity, grave: Entity, goal: Goal, solution: Solution) -> None:
    a.memes["shared_plan"] += 1
    b.memes["shared_plan"] += 1
    world.say(
        f"Then {a.id} took a breath and looked at {b.id}. {a.id} carried the {goal.carries}, while {b.id} "
        f"used careful paws to {goal.help_phrase}."
    )
    grave.meters["care"] += 1
    apply_solution(world, grave, solution)
    world.say(
        f"Together they made the {grave.label} look tidy and kind. The flowers stood straight, and the old stone "
        f"seemed less lonely."
    )


def ending(world: World, a: Entity, b: Entity, grave: Entity) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"In the end, {a.id} and {b.id} sat quietly beside the grave. They were no longer arguing. "
        f"They were proud that they had worked as a team."
    )
    world.say(
        f"The wind moved gently through the grass, and the grave stayed neat, covered in flowers and small kind acts."
    )


SETTINGS = {
    "quiet_garden": Setting("quiet_garden", "a quiet garden", "soft", ["rabbit", "mouse"]),
    "edge_wood": Setting("edge_wood", "the edge of the woods", "still", ["fox", "squirrel"]),
    "hill_path": Setting("hill_path", "a hill path", "cool", ["rabbit", "bird"]),
}

GOALS = {
    "flowers": Goal("flowers", "flowers", "place flowers on the grave", "arrange the petals", "carries", "flowers", {"grave", "flowers"}),
    "tidy": Goal("tidy", "tidy", "clean the grave stone", "wipe the stone smooth", "cloth", "tidy", {"grave", "clean"}),
}

PROBLEMS = {
    "grave_dirt": Problem("grave_dirt", "grave dirt", "the grave had dust and fallen leaves on it", "it would look uncared for", "the stone would stay dusty", {"grave", "dirt"}),
    "snapped_stem": Problem("snapped_stem", "snapped stem", "one flower stem had snapped in the basket", "the flowers would look messy", "the tribute would look half-finished", {"flowers", "grave"}),
}

SOLUTIONS = {
    "share_tasks": Solution("share_tasks", "share_tasks", 3, 2, "carefully brushed away the dirt, set the flowers in a bright cluster, and smiled as the grave looked loved again", "tried to work alone, but the job stayed messy", "brushed away the dirt and set the flowers in a bright cluster", {"grave", "teamwork"}),
    "smooth_stone": Solution("smooth_stone", "smooth_stone", 2, 1, "rubbed the stone smooth with the cloth and tucked the broken flower under the basket so it would not show", "rubbed at the stone, but the dirt clung stubbornly", "rubbed the stone smooth with the cloth", {"grave", "clean"}),
    "gentle_help": Solution("gentle_help", "gentle_help", 3, 2, "worked side by side, one holding the flowers and the other clearing the leaves, until the grave looked cared for", "worked side by side, but it was still too messy", "cleared the leaves until the grave looked cared for", {"grave", "teamwork"}),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: animals, a grave, conflict, and teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--animal1", choices=["rabbit", "fox", "mouse", "squirrel", "bird"])
    ap.add_argument("--animal2", choices=["rabbit", "fox", "mouse", "squirrel", "bird"])
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


def _pick_names(rng: random.Random) -> tuple[str, str]:
    names = ["Pip", "Milo", "Poppy", "Nina", "Toby", "Luna", "Bram", "Cleo"]
    a, b = rng.sample(names, 2)
    return a, b


def resolve_params(args: argparse.Namespace, rng: random.Random) -> "StoryParams":
    if args.problem and args.problem != "grave_dirt":
        raise StoryError("This world centers on grave dirt, because that creates the conflict and teamwork beat.")
    if args.solution and SOLUTIONS[args.solution].sense < 2:
        raise StoryError("That solution is too weak for this storyworld.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.goal is None or c[1] == args.goal)
              and (args.problem is None or c[2] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, goal, problem = rng.choice(combos)
    solution = args.solution or rng.choice(sorted(s.id for s in sensible_solutions()))
    n1, n2 = args.name1, args.name2
    if not n1 or not n2:
        n1, n2 = _pick_names(rng)
    a1 = args.animal1 or rng.choice(["rabbit", "fox", "mouse", "squirrel", "bird"])
    a2 = args.animal2 or rng.choice([x for x in ["rabbit", "fox", "mouse", "squirrel", "bird"] if x != a1])
    return StoryParams(setting, goal, problem, solution, n1, n2, a1, a2)


@dataclass
class StoryParams:
    setting: str
    goal: str
    problem: str
    solution: str
    name1: str
    name2: str
    animal1: str
    animal2: str
    seed: Optional[int] = None


def tell(params: StoryParams) -> World:
    world = World()
    s = SETTINGS[params.setting]
    g = GOALS[params.goal]
    p = PROBLEMS[params.problem]
    sol = SOLUTIONS[params.solution]
    a = world.add(Entity(params.name1, "character", params.animal1, role="friend", traits=["gentle"]))
    b = world.add(Entity(params.name2, "character", params.animal2, role="friend", traits=["thoughtful"]))
    grave = world.add(Entity("grave", "thing", "grave", label="the grave"))
    world.add(Entity("animals", "thing", "group", label="the two animals"))
    setup(world, s, a, b, g)
    world.para()
    conflict(world, a, b, g, p)
    _do_problem(world, grave, p)
    world.para()
    teamwork(world, a, b, grave, g, sol)
    ending(world, a, b, grave)
    world.facts.update(setting=s, goal=g, problem=p, solution=sol, a=a, b=b, grave=grave)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write an animal story about {f['a'].id} and {f['b'].id} at a grave, where they disagree at first but work together in the end.",
        f"Tell a gentle grave-side story for children that includes conflict and teamwork, with {f['goal'].label} as the shared task.",
        "Write a short animal story about a grave that becomes cared for after two friends stop arguing and help each other.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem("Who is the story about?", f"It is about {f['a'].id} and {f['b'].id}, two animal friends who went to the grave together. They started with a disagreement, but they learned to help each other."),
        QAItem("What problem did they face at the grave?", f"The grave had dirt and fallen leaves on it, so it looked uncared for. That made the friends want to fix it, but they argued about how to do it."),
        QAItem("How did they solve the problem?", f"They worked as a team. One animal held the flowers while the other cleared the leaves and brushed away the dirt, so the grave looked tidy again."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a grave?", "A grave is a place where a person or animal is buried and remembered. People often keep graves neat and may bring flowers to show care."),
        QAItem("What does teamwork mean?", "Teamwork means people help each other and do a job together. When teamwork works well, the task can get done more easily."),
        QAItem("Why can conflict be hard?", "Conflict can make friends upset because they disagree. If they calm down and listen, they can often find a better plan together."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
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
    return "\n".join(lines)


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


ASP_RULES = r"""
valid_combo(S, G, P) :- setting(S), goal(G), problem(P), P = grave_dirt.
story_ready :- valid_combo(_, _, _).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for gid in GOALS:
        lines.append(asp.fact("goal", gid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for sid in SOLUTIONS:
        lines.append(asp.fact("solution", sid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


CURATED = [
    StoryParams("quiet_garden", "flowers", "grave_dirt", "share_tasks", "Pip", "Milo", "rabbit", "mouse"),
    StoryParams("edge_wood", "flowers", "grave_dirt", "gentle_help", "Luna", "Toby", "fox", "squirrel"),
    StoryParams("hill_path", "tidy", "grave_dirt", "smooth_stone", "Cleo", "Bram", "bird", "rabbit"),
]


def build_curated() -> list[StoryParams]:
    return CURATED


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for combo in asp_valid_combos():
            print(" ", combo)
        return
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in build_curated()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random((args.seed or 0) + i))
            except StoryError as err:
                print(err)
                return
            params.seed = args.seed
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
