#!/usr/bin/env python3
"""
A small superhero story world about a kid hero solving a crooked problem with
grained clues, careful thinking, and a kind helper.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Place:
    id: str
    label: str
    where: str
    clue: str


@dataclass
class Problem:
    id: str
    label: str
    crooked: bool
    grained: bool
    needs: str
    blocks: str
    hint: str


@dataclass
class Tool:
    id: str
    label: str
    use: str
    fits: set[str] = field(default_factory=set)


@dataclass
class Hero:
    id: str
    name: str
    title: str
    kind: str
    power: str
    motto: str
    meme: str = "brave"


@dataclass
class World:
    place: Place
    problem: Problem
    tool: Tool
    hero: Hero
    helper: str
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    hero: str
    helper: str
    seed: Optional[int] = None


PLACES = {
    "rooftop": Place("rooftop", "the rooftop garden", "on the roof", "tiny pebbles and bent signs"),
    "alley": Place("alley", "the sunny alley", "between the shops", "chalk arrows and dust"),
    "playground": Place("playground", "the playground", "by the swings", "sand, paint, and footprints"),
}

PROBLEMS = {
    "stuck_gate": Problem(
        "stuck_gate",
        "a crooked gate",
        crooked=True,
        grained=False,
        needs="careful pushing",
        blocks="the path to the flower pots",
        hint="the hinge is bent the wrong way",
    ),
    "sandspill": Problem(
        "sandspill",
        "a grained sand spill",
        crooked=False,
        grained=True,
        needs="a steady sweep",
        blocks="the drain cover",
        hint="the grains keep sliding back into a pile",
    ),
    "tilted_sign": Problem(
        "tilted_sign",
        "a crooked sign",
        crooked=True,
        grained=False,
        needs="a straight lift",
        blocks="the way to the notice board",
        hint="the sign leans like it is trying to bow",
    ),
    "crumbled_path": Problem(
        "crumbled_path",
        "a grained, crooked path",
        crooked=True,
        grained=True,
        needs="a gentle repair",
        blocks="the shortcut to the bench",
        hint="the broken bits make the trail uneven",
    ),
}

TOOLS = {
    "gloves": Tool("gloves", "bright rescue gloves", "grip and lift tricky things", {"stuck_gate", "tilted_sign"}),
    "brush": Tool("brush", "a soft sweep brush", "gather loose grains without pushing them away", {"sandspill", "crumbled_path"}),
    "beam": Tool("beam", "a tiny light beam", "spot the best place to fix", {"stuck_gate", "sandspill", "tilted_sign", "crumbled_path"}),
    "rope": Tool("rope", "a red helper rope", "pull a crooked thing into line", {"stuck_gate", "tilted_sign"}),
}

HEROES = [
    Hero("spark", "Spark", "kid hero", "girl", "spot hidden trouble", "If it's crooked, I can help straighten the day!"),
    Hero("bolt", "Bolt", "kid hero", "boy", "solve with quick thinking", "First look, then act, then cheer!"),
    Hero("glimmer", "Glimmer", "young hero", "girl", "notice tiny clues", "Small clues can make a big fix!"),
]

HELPERS = ["a friendly pigeon", "the city gardener", "a small robot", "a laughing neighbor"]

GIRL_NAMES = ["Mina", "Lena", "Rosa", "Nora"]
BOY_NAMES = ["Ivo", "Taj", "Eli", "Otto"]


class WorldReason:
    @staticmethod
    def compatible(problem: Problem, tool: Tool) -> bool:
        return problem.id in tool.fits

    @staticmethod
    def honest_fix(problem: Problem, tool: Tool) -> bool:
        if problem.grained and tool.id == "gloves":
            return False
        if problem.crooked and tool.id == "brush" and problem.id == "stuck_gate":
            return False
        return WorldReason.compatible(problem, tool)


ASP_RULES = r"""
problem(P) :- crooked_problem(P).
problem(P) :- grained_problem(P).

can_use(T,P) :- tool(T), problem(P), fits(T,P).
honest_fix(P,T) :- can_use(T,P), not bad_match(P,T).

valid_story(Place,Prob,Tool) :- place(Place), problem(Prob), tool(Tool), honest_fix(Prob,Tool).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
    for pr in PROBLEMS.values():
        lines.append(asp.fact("problem", pr.id))
        if pr.crooked:
            lines.append(asp.fact("crooked_problem", pr.id))
        if pr.grained:
            lines.append(asp.fact("grained_problem", pr.id))
    for t in TOOLS.values():
        lines.append(asp.fact("tool", t.id))
        for p in sorted(t.fits):
            lines.append(asp.fact("fits", t.id, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero story world about problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = []
    for pid, pr in PROBLEMS.items():
        for tid, tool in TOOLS.items():
            if not WorldReason.honest_fix(pr, tool):
                continue
            for place in PLACES:
                combos.append((place, pid, tid))
    combos = [c for c in combos
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, tool = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, problem=problem, tool=tool, hero=hero, helper=helper)


def make_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]
    hero = next((h for h in HEROES if h.name.lower().startswith(params.hero.lower()[0])), HEROES[0])
    hero = Hero(hero.id, params.hero, hero.title, hero.kind, hero.power, hero.motto, hero.meme)
    world = World(place=place, problem=problem, tool=tool, hero=hero, helper=params.helper)
    world.facts = {"place": place, "problem": problem, "tool": tool, "hero": hero, "helper": params.helper}
    return world


def tell(world: World) -> None:
    h = world.hero
    p = world.problem
    pl = world.place
    t = world.tool
    helper = world.helper

    world.say(f"{h.name} was a little {h.title} who loved to solve tricky problems.")
    world.say(f"One day, {h.name} noticed {p.label} at {pl.label}. It was {p.hint}.")
    world.say(f"{h.name} pointed at it and said, \"{h.motto}\" {helper} nodded, because the problem blocked {p.blocks}.")
    world.para()
    world.say(f"{h.name} studied the scene, then picked up {t.label}.")
    if p.grained:
        world.say(f"The grained bits needed {p.needs}, so {h.name} used {t.use}.")
    if p.crooked:
        world.say(f"The crooked shape needed a careful fix, not a fast push.")
    if WorldReason.honest_fix(p, t):
        world.say(f"With a calm breath, {h.name} made the fix step by step.")
        world.say(f"Soon the problem was straightened out, and the path opened again.")
        world.para()
        world.say(f"At the end, {h.name} stood beside {helper}, smiling at the clear way ahead.")
    else:
        raise StoryError("The chosen tool does not honestly solve this problem.")


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a short superhero story about {world.hero.name} solving {world.problem.label} at {world.place.label}.",
        f"Tell a child-friendly story where a hero uses {world.tool.label} to fix a crooked or grained problem.",
        f"Write a gentle problem-solving superhero story with the words 'grained' and 'crooked'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question=f"Who solves the problem in the story?",
            answer=f"{world.hero.name} solves it by looking carefully, choosing {world.tool.label}, and fixing the trouble step by step.",
        ),
        QAItem(
            question=f"What kind of problem did {world.hero.name} find?",
            answer=f"{world.hero.name} found {world.problem.label}, which was {world.problem.hint} and blocked {world.problem.blocks}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the problem fixed, the way opened again, and {world.hero.name} smiling beside {world.helper}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean when something is crooked?",
            answer="Crooked means it is bent, twisted, or not straight.",
        ),
        QAItem(
            question="What does grained mean?",
            answer="Grained means made of small little bits or grains, like sand or tiny crumbs.",
        ),
        QAItem(
            question="Why do heroes use tools when solving problems?",
            answer="Heroes use tools because the right tool can help them fix a problem safely and carefully.",
        ),
    ]


def dump_trace(world: World) -> str:
    return "\n".join([
        "--- world model state ---",
        f"place={world.place.id}",
        f"problem={world.problem.id}",
        f"tool={world.tool.id}",
        f"hero={world.hero.name}",
        f"helper={world.helper}",
    ])


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell(world)
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
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def verify() -> int:
    import asp
    program = asp_program("#show honest_fix/2.")
    model = asp.one_model(program)
    asp_pairs = set(asp.atoms(model, "honest_fix"))
    py_pairs = set((p.id, t.id) for p in PROBLEMS.values() for t in TOOLS.values() if WorldReason.honest_fix(p, t))
    if asp_pairs == py_pairs:
        print(f"OK: clingo gate matches python gate ({len(py_pairs)} combos).")
        return 0
    print("MISMATCH between clingo and python gates.")
    print("only in clingo:", sorted(asp_pairs - py_pairs))
    print("only in python:", sorted(py_pairs - asp_pairs))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show honest_fix/2."))
    return sorted(set(asp.atoms(model, "honest_fix")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show honest_fix/2."))
        return
    if args.verify:
        sys.exit(verify())
    if args.asp:
        combos = asp_valid_combos()
        for p, t in combos:
            print(p, t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("rooftop", "stuck_gate", "gloves", "Spark", "a friendly pigeon"),
            StoryParams("alley", "sandspill", "brush", "Bolt", "the city gardener"),
            StoryParams("playground", "tilted_sign", "rope", "Glimmer", "a small robot"),
            StoryParams("playground", "crumbled_path", "brush", "Mina", "a laughing neighbor"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
