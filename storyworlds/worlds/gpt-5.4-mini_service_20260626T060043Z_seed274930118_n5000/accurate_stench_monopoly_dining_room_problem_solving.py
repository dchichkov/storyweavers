#!/usr/bin/env python3
"""
A storyworld for a tiny pirate-style dining-room tale with a stinky monopoly problem,
where teamwork and careful problem solving turn conflict into a clever fix.
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

ACCENT_WORDS = ("accurate", "stench", "monopoly")


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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "dad", "captain"}
        female = {"girl", "woman", "mother", "mom"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the dining room"
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    smell: str
    cause: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    label: str
    phrase: str
    method: str
    tail: str
    fixes: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    problem: str
    solution: str
    hero: str
    sidekick: str
    rival: str
    seed: Optional[int] = None


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
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


def _r_stench(world: World) -> list[str]:
    out = []
    for ent in world.entities.values():
        if ent.meters.get("stench", 0) < 1:
            continue
        if ("stench_notice", ent.id) in world.fired:
            continue
        world.fired.add(("stench_notice", ent.id))
        ent.memes["trouble"] = ent.memes.get("trouble", 0) + 1
        out.append(f"The air grew foul around {ent.label}.")
    return out


def _r_conflict(world: World) -> list[str]:
    hero = world.get("hero")
    rival = world.get("rival")
    if hero.memes.get("angry", 0) < 1:
        return []
    if ("conflict", hero.id) in world.fired:
        return []
    world.fired.add(("conflict", hero.id))
    hero.memes["conflict"] = hero.memes.get("conflict", 0) + 1
    rival.memes["conflict"] = rival.memes.get("conflict", 0) + 1
    return ["The two pirates crossed their arms and glared."]


def _r_fix(world: World) -> list[str]:
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    problem = world.get("problem")
    solution = world.get("solution")
    if hero.memes.get("conflict", 0) < 1:
        return []
    if solution.worn_by != hero.id:
        return []
    if ("fix", problem.id) in world.fired:
        return []
    world.fired.add(("fix", problem.id))
    problem.meters["cleared"] = 1
    hero.memes["calm"] = hero.memes.get("calm", 0) + 1
    sidekick.memes["pride"] = sidekick.memes.get("pride", 0) + 1
    return [f"{hero.label} and {sidekick.label} used the plan and set things right."]


def propagate(world: World) -> list[str]:
    out = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_stench, _r_conflict, _r_fix):
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    for s in out:
        world.say(s)
    return out


SETTING = Setting(place="the dining room", affords={"beans"})
PROBLEMS = {
    "stench": Problem(
        id="stench",
        label="a rotten fish smell",
        phrase="an awful stench from the pantry",
        smell="stench",
        cause="a spilled barrel of fish",
        zone={"nose", "table"},
        keyword="stench",
        tags={"stench", "problem"},
    ),
    "monopoly": Problem(
        id="monopoly",
        label="a monopoly map",
        phrase="an accurate monopoly map",
        smell="stench",
        cause="a fish-stained chart nobody could read",
        zone={"hands", "table"},
        keyword="monopoly",
        tags={"monopoly", "accurate"},
    ),
}
SOLUTIONS = {
    "air": Solution(
        id="air",
        label="open windows",
        phrase="open windows and a fresh sea breeze",
        method="unbar the windows",
        tail="let the sea breeze carry the stink away",
        fixes={"stench"},
        covers=set(),
    ),
    "map": Solution(
        id="map",
        label="an accurate map",
        phrase="an accurate, dry copy of the map",
        method="make a clean copy",
        tail="helped everyone agree on the route",
        fixes={"monopoly"},
        covers={"hands", "table"},
    ),
    "team": Solution(
        id="team",
        label="a teamwork plan",
        phrase="a teamwork plan with cloths, ropes, and a bucket",
        method="work together",
        tail="proved the crew could solve trouble together",
        fixes={"stench", "monopoly"},
        covers={"hands", "table", "nose"},
    ),
}

HEROES = ["Captain Mina", "Captain Jory", "Captain Isla", "Captain Bram"]
SIDEKICKS = ["First Mate Pip", "First Mate Nell", "First Mate Bo", "First Mate Kest"]
RIVALS = ["Old Salt Rook", "Brine Beard", "Nip the Nasty", "Captain Crow"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, p in PROBLEMS.items():
        for sid, s in SOLUTIONS.items():
            if p.id in s.fixes:
                combos.append((pid, sid))
    return combos


def reason_gate(problem: Problem, solution: Solution) -> bool:
    return problem.id in solution.fixes


def explain_rejection(problem: Problem, solution: Solution) -> str:
    return (
        f"(No story: {solution.label} does not really solve {problem.label}. "
        f"Try a fix that matches the trouble.)"
    )


def tell(problem: Problem, solution: Solution, hero_name: str, sidekick_name: str, rival_name: str) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id="hero", kind="character", type="captain", label=hero_name))
    sidekick = world.add(Entity(id="sidekick", kind="character", type="mate", label=sidekick_name))
    rival = world.add(Entity(id="rival", kind="character", type="captain", label=rival_name))
    problem_ent = world.add(Entity(id="problem", type="thing", label=problem.label, phrase=problem.phrase))
    solution_ent = world.add(Entity(id="solution", type="thing", label=solution.label, phrase=solution.phrase, owner=hero.id))
    world.facts.update(problem=problem_ent, solution=solution_ent, hero=hero, sidekick=sidekick, rival=rival)

    world.say(
        f"In {SETTING.place}, {hero_name} and {sidekick_name} were trying to keep a proper pirate supper."
    )
    world.say(
        f"But {problem.phrase} drifted through the room, and even the lanterns seemed to wrinkle their noses."
    )
    world.para()
    world.say(
        f"{rival_name} banged the table and demanded to keep the monopoly map all to {rival.pronoun('possessive')}self."
    )
    world.say(
        f"{hero_name} frowned, because that was neither fair nor accurate."
    )
    hero.memes["angry"] = 1
    problem_ent.meters["stench"] = 1
    if problem.id == "monopoly":
        problem_ent.meters["blocked"] = 1
    propagate(world)
    world.para()
    if solution.id == "team":
        world.say(f"{sidekick_name} said, 'Let's solve it together.'")
        world.say(
            f"So the crew used {solution.phrase}, and {hero_name} {solution.method}, while {sidekick_name} hauled a bucket and wiped the table."
        )
    elif solution.id == "air":
        world.say(f"{hero_name} spotted the problem and chose to {solution.method}.")
        world.say(f"Then {solution.tail}, and the dining room breathed easy again.")
    else:
        world.say(f"{hero_name} promised to {solution.method}, because the chart had to be clear and accurate.")
        world.say(f"That small fix {solution.tail}.")
    problem_ent.meters["cleared"] = 1
    hero.memes["conflict"] = 0
    sidekick.memes["teamwork"] = 1
    world.para()
    world.say(
        f"In the end, the supper stayed peaceful, the stench was gone, and the pirates could share the table like a real crew."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short pirate tale set in {world.setting.place} about {f['hero'].label}, {f['sidekick'].label}, and a smelly problem that needs solving.",
        f"Tell a child-friendly story where teamwork helps {f['hero'].label} fix an accurate but troublesome pirate matter.",
        f"Write a tiny adventure with conflict, problem solving, and a dining-room surprise involving {f['problem'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"What trouble was in the dining room?",
            answer=f"There was {f['problem'].phrase}, which made the room smell bad and caused trouble for the pirates.",
        ),
        QAItem(
            question=f"Who helped solve the problem with {f['hero'].label}?",
            answer=f"{f['sidekick'].label} helped {f['hero'].label} solve it by using teamwork and a careful plan.",
        ),
        QAItem(
            question=f"Why did the pirates argue at first?",
            answer=f"They argued because {f['rival'].label} wanted to keep the monopoly map instead of sharing it fairly.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The stench was gone, the conflict cooled down, and the pirates shared the dining room peacefully.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and do jobs together to solve a problem.",
        ),
        QAItem(
            question="What is conflict?",
            answer="Conflict is a disagreement or fight between people who want different things.",
        ),
        QAItem(
            question="What does accurate mean?",
            answer="Accurate means correct and carefully right, not mixed up or wrong.",
        ),
        QAItem(
            question="What is a stench?",
            answer="A stench is a very strong bad smell.",
        ),
        QAItem(
            question="What is a monopoly?",
            answer="A monopoly is when one person or group tries to keep control of something and not share it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} label={e.label} meters={meters} memes={memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(problem="stench", solution="air", hero="Captain Mina", sidekick="First Mate Pip", rival="Old Salt Rook"),
    StoryParams(problem="monopoly", solution="map", hero="Captain Jory", sidekick="First Mate Nell", rival="Brine Beard"),
    StoryParams(problem="monopoly", solution="team", hero="Captain Isla", sidekick="First Mate Bo", rival="Captain Crow"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("tagged", pid, t))
    for sid, s in SOLUTIONS.items():
        lines.append(asp.fact("solution", sid))
        for f in sorted(s.fixes):
            lines.append(asp.fact("fixes", sid, f))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,S) :- problem(P), solution(S), fixes(S,P).
#show valid/2.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate dining-room storyworld with stench, monopoly, teamwork, and conflict.")
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
    ap.add_argument("--rival")
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
    combos = valid_combos()
    if args.problem and args.solution:
        if not reason_gate(PROBLEMS[args.problem], SOLUTIONS[args.solution]):
            raise StoryError(explain_rejection(PROBLEMS[args.problem], SOLUTIONS[args.solution]))
        combos = [c for c in combos if c == (args.problem, args.solution)]
    else:
        if args.problem:
            combos = [c for c in combos if c[0] == args.problem]
        if args.solution:
            combos = [c for c in combos if c[1] == args.solution]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    problem, solution = rng.choice(sorted(combos))
    return StoryParams(
        problem=problem,
        solution=solution,
        hero=args.hero or rng.choice(HEROES),
        sidekick=args.sidekick or rng.choice(SIDEKICKS),
        rival=args.rival or rng.choice(RIVALS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(PROBLEMS[params.problem], SOLUTIONS[params.solution], params.hero, params.sidekick, params.rival)
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid problem/solution combos:\n")
        for p, s in combos:
            print(f"{p:10} {s}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
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
            header = f"### {p.hero}: {p.problem} -> {p.solution}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
