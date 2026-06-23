#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T042304Z_seed1855084837_n10/avalanche_problem_solving_teamwork_comedy.py
=============================================================================================================

A small comedy storyworld about a team who faces an avalanche, solves the
problem together, and learns to work as a team.

The world model tracks physical meters and emotional memes for a few typed
entities. The story is generated from state, not from a frozen paragraph.
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
from typing import Optional

# Make shared results importable from nested output directories.
_HERE = os.path.abspath(__file__)
_SEARCH = os.path.dirname(_HERE)
while True:
    if os.path.exists(os.path.join(_SEARCH, "results.py")):
        if _SEARCH not in sys.path:
            sys.path.insert(0, _SEARCH)
        break
    parent = os.path.dirname(_SEARCH)
    if parent == _SEARCH:
        raise RuntimeError("Could not locate storyworlds/results.py")
    _SEARCH = parent

from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    terrain: str = ""
    slope: str = ""
    affords: set[str] = field(default_factory=set)


@dataclass
class TeamRole:
    id: str
    label: str
    job: str
    tool: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    danger: str
    mess: str
    cover: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    method: str
    result: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.history: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.history = list(self.history)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    leader: str
    problem: str
    fix: str
    seed: Optional[int] = None


PLACES = {
    "ski_hut": Place("ski_hut", "the ski hut", terrain="snowy hill", slope="steep slope", affords={"avalanche"}),
    "ridge": Place("ridge", "the ridge", terrain="windy ridge", slope="narrow trail", affords={"avalanche"}),
}

TEAM_ROLES = {
    "map": TeamRole("map", "the map reader", "reads the map", "a map", tags={"problem_solving", "teamwork"}),
    "rope": TeamRole("rope", "the rope holder", "holds the rope", "a rope", tags={"problem_solving", "teamwork"}),
    "shovel": TeamRole("shovel", "the shovel runner", "runs the shovel", "a shovel", tags={"problem_solving", "teamwork"}),
}

PROBLEMS = {
    "avalanche": Problem("avalanche", "an avalanche", "snow is sliding fast", "snow piling up on the trail", "a safe path", tags={"avalanche"}),
}

FIXES = {
    "signal": Fix("signal", "a whistle signal", "blow the whistle and point", "everyone moves together", tags={"problem_solving", "teamwork"}),
    "chain": Fix("chain", "a human chain", "link arms and move snow buckets", "the path clears in a silly hurry", tags={"problem_solving", "teamwork"}),
}

NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Theo", "Zoe", "Finn"]
TRAITS = ["cheerful", "clumsy", "curious", "brave", "silly"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        if "avalanche" not in place.affords:
            continue
        for problem_id in PROBLEMS:
            for fix_id in FIXES:
                combos.append((place_id, problem_id, fix_id, "team"))
    return combos


def avalanche_at_risk(problem: Problem, place: Place) -> bool:
    return problem.id == "avalanche" and "avalanche" in place.affords


def best_fix(problem: Problem, fix: Fix) -> bool:
    return "problem_solving" in fix.tags and "teamwork" in fix.tags


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about an avalanche, teamwork, and problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--leader")
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
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place_id, problem_id, fix_id, _ = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != hero])
    leader = args.leader or rng.choice([n for n in NAMES if n not in {hero, helper}])
    return StoryParams(place=place_id, hero=hero, helper=helper, leader=leader, problem=problem_id, fix=fix_id)


def _setup(world: World, params: StoryParams) -> tuple[Entity, Entity, Entity]:
    hero = world.add(Entity(id=params.hero, kind="character", type="boy", role="hero"))
    helper = world.add(Entity(id=params.helper, kind="character", type="girl", role="helper"))
    leader = world.add(Entity(id=params.leader, kind="character", type="boy", role="leader"))
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    leader.memes["joy"] += 1
    return hero, helper, leader


def _start_problem(world: World, leader: Entity, problem: Problem) -> None:
    leader.memes["worry"] += 1
    world.add(Entity(id="snow", kind="thing", type="snow", label="snowbank"))
    world.get("snow").meters["sliding"] += 1
    world.say(f"In {world.place.label}, the team spotted {problem.label} near {world.place.slope}.")
    world.say(f"Then the snow started to wobble, which is a very rude way for a hill to begin a meeting.")


def _panic_or_plan(world: World, hero: Entity, helper: Entity, leader: Entity, fix: Fix) -> None:
    hero.memes["surprise"] += 1
    helper.memes["focus"] += 1
    leader.memes["focus"] += 1
    world.say(f"{hero.id} yelled, \"Uh-oh, the mountain is doing cartwheels!\"")
    world.say(f"{helper.id} said, \"That is definitely an avalanche, and I would prefer it not invent new stairs.\"")
    world.say(f"{leader.id} pointed and said, \"No shouting separately. Let's solve this together.\"")
    world.say(f"They picked {fix.label} because it was a teamwork kind of fix.")


def _resolve(world: World, hero: Entity, helper: Entity, leader: Entity, fix: Fix, problem: Problem) -> None:
    hero.meters["helped"] += 1
    helper.meters["helped"] += 1
    leader.meters["helped"] += 1
    hero.memes["pride"] += 1
    helper.memes["pride"] += 1
    leader.memes["pride"] += 1
    world.say(f"They {fix.method}, and {fix.result}.")
    world.say(f"The avalanche slowed, then stopped with a soft snowy sigh, as if it had simply forgotten its lines.")
    world.say(f"Afterward, the team laughed, brushed snow from their hats, and made a new path past {problem.label}.")


def _end_image(world: World, hero: Entity, helper: Entity, leader: Entity) -> None:
    world.say(f"By the end, {hero.id}, {helper.id}, and {leader.id} were lined up like proud snow statues, grinning in the sunshine.")
    world.say("The trail was clear, the problem was solved, and the biggest joke of the day was how serious everyone had looked while saving a hill.")


def tell(place: Place, problem: Problem, fix: Fix, hero: str, helper: str, leader: str) -> World:
    world = World(place)
    h, he, l = _setup(world, StoryParams(place=place.id, hero=hero, helper=helper, leader=leader, problem=problem.id, fix=fix.id))
    _start_problem(world, l, problem)
    world.para()
    _panic_or_plan(world, h, he, l, fix)
    world.para()
    _resolve(world, h, he, l, fix, problem)
    world.para()
    _end_image(world, h, he, l)
    world.facts.update(place=place, problem=problem, fix=fix, hero=h, helper=he, leader=l, solved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny short story for a young child about {f["hero"].id}, {f["helper"].id}, and {f["leader"].id} facing {f["problem"].label} at {f["place"].label}.',
        f"Tell a comedy story where a team solves an avalanche problem together instead of panicking.",
        f'Write a teamwork story that includes the word "avalanche" and ends with everyone laughing after fixing the path.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, leader = f["hero"], f["helper"], f["leader"]
    place, problem, fix = f["place"], f["problem"], f["fix"]
    return [
        QAItem(
            question=f"Who worked together when {problem.label} happened at {place.label}?",
            answer=f"{hero.id}, {helper.id}, and {leader.id} worked together. They stayed calm enough to make a plan instead of turning the avalanche into a bigger mess.",
        ),
        QAItem(
            question=f"What problem did the team solve in {place.label}?",
            answer=f"They solved {problem.label}. The snow was sliding fast, so they needed to act as a team and choose a fix that could actually clear the path.",
        ),
        QAItem(
            question=f"How did {fix.label} help the team?",
            answer=f"They used {fix.method}, and that let everyone move together. It worked because the fix was good for problem solving and teamwork, not just for looking impressive.",
        ),
        QAItem(
            question=f"What showed that the story ended happily?",
            answer=f"By the end, the trail was clear and the three friends were grinning together. That ending image proves the avalanche problem was solved and the team was stronger for it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem("What is an avalanche?", "An avalanche is a lot of snow sliding quickly down a mountain. It can block a trail and make the ground dangerous."),
        QAItem("Why is teamwork useful?", "Teamwork is useful because different people can help in different ways. When a group shares the job, hard problems can get solved faster."),
        QAItem("What does problem solving mean?", "Problem solving means figuring out what to do when something goes wrong. You look at the trouble, make a plan, and try the best fix."),
    ]
    return out


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="ski_hut", hero="Mia", helper="Leo", leader="Nora", problem="avalanche", fix="signal"),
    StoryParams(place="ridge", hero="Ava", helper="Theo", leader="Finn", problem="avalanche", fix="chain"),
    StoryParams(place="ski_hut", hero="Zoe", helper="Ben", leader="Leo", problem="avalanche", fix="chain"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for fid in FIXES:
        lines.append(asp.fact("fix", fid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, Prob, Fix) :- place(P), problem(Prob), fix(Fix), affords(P, Prob).
teamwork(Fix) :- fix(Fix).
problem_solving(Fix) :- fix(Fix).
"""


def asp_program(show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    gate = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = 0
    if gate != cl:
        print("MISMATCH between Python and ASP valid_combos()")
        print("python only:", sorted(gate - cl))
        print("asp only:", sorted(cl - gate))
        ok = 1
    else:
        print(f"OK: ASP matches valid_combos() ({len(gate)} combos).")
    try:
        sample = generate(CURATED[0])
        if not sample.story or not sample.story_qa:
            raise RuntimeError("empty sample")
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"FAIL: generate() smoke test failed: {e}")
        return 1
    return ok


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.problem not in PROBLEMS or params.fix not in FIXES:
        raise StoryError("Invalid story params.")
    if not avalanche_at_risk(PROBLEMS[params.problem], PLACES[params.place]):
        raise StoryError("This place does not fit an avalanche story.")
    world = tell(PLACES[params.place], PROBLEMS[params.problem], FIXES[params.fix], params.hero, params.helper, params.leader)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
