#!/usr/bin/env python3
"""
storyworlds/worlds/waylay_problem_solving_nursery_rhyme.py
============================================================

A standalone story world based on a nursery‑rhyme domain: a little creature sets
out, is *waylaid* by an obstacle, and solves the problem.  The story is driven
by state changes (meters/memes) and rendered in rhyming couplets.

Initial seed story (paraphrased as a nursery rhyme):
---
Little Timmy Mouse
Went out of his house.
A big log lay across the track ―
“Oh no, I cannot get back!”
But Timmy found a plank so wide,
He laid it down and crossed with pride.
Now Timmy Mouse can go and play,
He found a clever way today.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Entity
# ---------------------------------------------------------------------------
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"mother", "aunt", "hen", "duck"}
        male = {"father", "uncle", "mouse", "rabbit", "badger"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class Path:
    name: str
    description: str
    rhyme_line: str

@dataclass
class Obstacle:
    id: str
    label: str
    rhyme_encounter: str
    kind: str = "physical"  # physical | social

@dataclass
class Solution:
    id: str
    label: str
    rhyme_use: str
    fixes: set[str]

@dataclass
class StoryParams:
    path: str
    obstacle: str
    solution: str
    hero_name: str
    hero_type: str
    trait: str
    seed: Optional[int] = None

# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[str] = []
        self.obstacle: Optional[Obstacle] = None
        self.solution: Optional[Solution] = None
        self.hero: Optional[Entity] = None

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs.append(text)

    def render(self) -> str:
        return "\n".join(self.paragraphs)

    def copy(self) -> "World":
        clone = World(self.path)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.obstacle = self.obstacle
        clone.solution = self.solution
        return clone

# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

def _r_waylay(world: World) -> list[str]:
    """When hero encounters obstacle, raise frustration and stop progress."""
    hero = world.hero
    if hero is None:
        return []
    if hero.memes["progress"] >= THRESHOLD:
        return []
    if world.obstacle is None:
        return []
    sig = ("waylay", hero.id, world.obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["frustration"] += 1
    hero.memes["progress"] = 0.0
    return [world.obstacle.rhyme_encounter]

def _r_solve(world: World) -> list[str]:
    hero = world.hero
    if hero is None or world.solution is None:
        return []
    if hero.memes["frustration"] < THRESHOLD:
        return []
    if hero.memes["solved"] >= THRESHOLD:
        return []
    sig = ("solve", hero.id, world.solution.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["solved"] += 1
    hero.memes["joy"] += 1
    hero.memes["progress"] += 1
    hero.memes["frustration"] = 0.0
    return [world.solution.rhyme_use]

CAUSAL_RULES = [
    Rule(name="waylay", apply=_r_waylay),
    Rule(name="solve", apply=_r_solve),
]

def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced

# ---------------------------------------------------------------------------
# Screenplay (verbs)
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    world.say(f"Little {hero.type} {hero.id}")
    world.say(f"Went out of {hero.pronoun('possessive')} house one day.")

def start_walk(world: World, path: Path) -> None:
    world.say(path.rhyme_line)

def waylay_rhyme(world: World, obstacle: Obstacle) -> None:
    world.obstacle = obstacle
    propagate(world)

def solve_rhyme(world: World, solution: Solution) -> None:
    world.solution = solution
    propagate(world)

def ending(world: World, hero: Entity) -> None:
    world.say(f"Now {hero.type} {hero.id} can go and play,")
    world.say(f"{hero.pronoun('possessive').capitalize()} found a clever way today.")

# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PATHS = {
    "meadow": Path(name="meadow", description="a sunny meadow path",
                   rhyme_line="The path went through the meadow bright,"),
    "forest": Path(name="forest", description="a shady forest trail",
                   rhyme_line="Into the woods, a tiny trail,"),
    "bridge": Path(name="bridge", description="a little wooden bridge",
                   rhyme_line="Across the brook a bridge did sway,"),
}

OBSTACLES = {
    "log": Obstacle(id="log", label="a fallen log",
                    rhyme_encounter="A big log lay across the track —\n"Oh no, I cannot get back!""),
    "stream": Obstacle(id="stream", label="a babbling stream",
                       rhyme_encounter="A babbling stream blocked the way,\nThe water made the path delay."),
    "troll": Obstacle(id="troll", label="a cranky troll",
                      rhyme_encounter="A cranky troll sat on the stone,\n"You cannot cross here all alone!""),
}

SOLUTIONS = {
    "plank": Solution(id="plank", label="a sturdy plank",
                      rhyme_use="But {hero} found a plank so wide,\nHe laid it down and crossed with pride.",
                      fixes={"log", "stream"}),
    "stones": Solution(id="stones", label="stepping stones",
                       rhyme_use="Then {hero} saw some stones so neat,\nAnd hopped across on happy feet.",
                       fixes={"stream"}),
    "polite": Solution(id="polite", label="a polite request",
                       rhyme_use="{hero} smiled and said "Please, sir,"\nThe troll let {hero} cross with her.",
                       fixes={"troll"}),
}

HERO_NAMES = {"mouse": ["Timmy", "Minnie"], "rabbit": ["Bunny", "Hopsy"], "squirrel": ["Nutty", "Squeaky"]}
TRAITS = ["brave", "clever", "kind", "patient", "curious"]

def valid_solution(obstacle_id: str, solution_id: str) -> bool:
    return obstacle_id in SOLUTIONS[solution_id].fixes

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for path in PATHS:
        for obs in OBSTACLES:
            for sol in SOLUTIONS:
                if valid_solution(obs, sol):
                    combos.append((path, obs, sol))
    return combos

# ---------------------------------------------------------------------------
# Tell the story
# ---------------------------------------------------------------------------
def tell(path_id: str, obstacle_id: str, solution_id: str,
         hero_name: str, hero_type: str, trait: str) -> World:
    path = PATHS[path_id]
    obstacle = OBSTACLES[obstacle_id]
    solution = SOLUTIONS[solution_id]

    world = World(path)
    hero = Entity(id=hero_name, kind="character", type=hero_type,
                  traits=[trait, "little"])
    world.add(hero)
    world.hero = hero

    # Act 1
    introduce(world, hero)
    start_walk(world, path)

    # Act 2
    waylay_rhyme(world, obstacle)

    # Act 3
    solve_rhyme(world, solution)
    ending(world, hero)

    return world

# ---------------------------------------------------------------------------
# Q&A generators
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.hero
    obs = world.obstacle
    sol = world.solution
    return [
        f"Write a nursery rhyme about a little {f.type} who meets a {obs.label} and finds a clever solution.",
        f"Tell a short rhyming story where a {f.type} named {f.id} uses a {sol.label} to solve a problem.",
        f"Create a children's poem about problem solving, using the words '{obs.id}' and '{sol.id}'.",
    ]

def story_qa(world: World) -> list[QAItem]:
    hero = world.hero
    obs = world.obstacle
    sol = world.solution
    path = world.path
    qa = [
        QAItem(
            question=f"Who is the story about and where did {hero.pronoun()} go?",
            answer=f"The story is about a little {hero.type} named {hero.id}. {hero.pronoun().capitalize()} went out onto {path.description}."
        ),
        QAItem(
            question=f"What problem did {hero.id} meet on the way?",
            answer=f"{hero.id} met {obs.label} blocking the path. {obs.rhyme_encounter.replace(chr(10), ' ').replace('"','')}"
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem?",
            answer=f"{hero.id} used {sol.label} to get past the problem. {sol.rhyme_use.replace('{hero}', hero.id).replace(chr(10), ' ')}"
        ),
        QAItem(
            question=f"Was {hero.id} brave or clever to find a way?",
            answer=f"{hero.id} was very {hero.traits[0]} and {hero.traits[1] if len(hero.traits)>1 else 'clever'}. {hero.pronoun().capitalize()} did not give up."
        ),
    ]
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    # generic child‑friendly facts about paths, logs, streams, trolls
    return [
        QAItem(
            question="What is a path?",
            answer="A path is a narrow way that people or animals walk on, often through a forest or meadow."
        ),
        QAItem(
            question="Why can a fallen log block the way?",
            answer="A fallen log lies across the path and is too big to step over easily. You have to go around it or find a plank."
        ),
        QAItem(
            question="What is a troll?",
            answer="In stories, a troll is a make‑believe creature that lives under bridges. Sometimes it is grumpy and does not let you cross."
        ),
        QAItem(
            question="How can stepping stones help you cross a stream?",
            answer="Stepping stones are flat rocks placed in the water so you can hop from one to the other without getting wet."
        ),
    ]

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  obstacle: {world.obstacle.id if world.obstacle else 'None'}")
    lines.append(f"  solution: {world.solution.id if world.solution else 'None'}")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# Clingo ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid_combo(P, O, S) :- path(P), obstacle(O), solution(S), fixes(S,O).
"""

def asp_facts() -> str:
    import asp  # lazy
    lines = []
    for pid in PATHS:
        lines.append(asp.fact("path", pid))
    for oid in OBSTACLES:
        lines.append(asp.fact("obstacle", oid))
    for sid, sol in SOLUTIONS.items():
        lines.append(asp.fact("solution", sid))
        for f in sol.fixes:
            lines.append(asp.fact("fixes", sid, f))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))

def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1

# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery rhyme storyworld: a little creature is waylaid and solves a problem.")
    ap.add_argument("--path", choices=list(PATHS))
    ap.add_argument("--obstacle", choices=list(OBSTACLES))
    ap.add_argument("--solution", choices=list(SOLUTIONS))
    ap.add_argument("--hero-type", choices=list(HERO_NAMES))
    ap.add_argument("--name")
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
    if args.obstacle and args.solution:
        if not valid_solution(args.obstacle, args.solution):
            raise StoryError(
                f"(No story: {args.solution} does not fix {args.obstacle}.)")
    combos = [c for c in valid_combos()
              if (args.path is None or c[0] == args.path)
              and (args.obstacle is None or c[1] == args.obstacle)
              and (args.solution is None or c[2] == args.solution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    path, obs, sol = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(list(HERO_NAMES))
    name = args.name or rng.choice(HERO_NAMES[hero_type])
    trait = rng.choice(TRAITS)
    return StoryParams(path=path, obstacle=obs, solution=sol,
                       hero_name=name, hero_type=hero_type, trait=trait)

def generate(params: StoryParams) -> StorySample:
    # Format solution rhyme with hero name
    sol = SOLUTIONS[params.solution]
    sol_rhyme = sol.rhyme_use.replace("{hero}", params.hero_name)
    SOLUTIONS[params.solution] = Solution(sol.id, sol.label, sol_rhyme, sol.fixes)

    world = tell(params.path, params.obstacle, params.solution,
                 params.hero_name, params.hero_type, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for p, o, s in combos:
            print(f"  path={p:8} obstacle={o:8} solution={s}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        # Use a curated set of valid combos
        curated = [
            StoryParams(path="meadow", obstacle="log", solution="plank",
                        hero_name="Timmy", hero_type="mouse", trait="brave"),
            StoryParams(path="forest", obstacle="stream", solution="stones",
                        hero_name="Bunny", hero_type="rabbit", trait="clever"),
            StoryParams(path="bridge", obstacle="troll", solution="polite",
                        hero_name="Minnie", hero_type="mouse", trait="kind"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
            params.seed = seed
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
            header = f"### {p.hero_name} at {p.path} (obstacle: {p.obstacle})"
        elif len(samples) > 1:
            header = f"### variant {i+1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples)-1:
            print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
