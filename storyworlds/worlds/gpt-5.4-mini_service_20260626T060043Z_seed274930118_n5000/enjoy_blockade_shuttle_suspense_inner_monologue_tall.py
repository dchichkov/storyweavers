#!/usr/bin/env python3
"""
A standalone storyworld for a Tall Tale about a shuttle, a blockade, and a
careful plan that turns suspense into relief.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, replace
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carries: set[str] = field(default_factory=set)
    blocked_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.type

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "pilot", "boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother", "navigator"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the sky road"
    tall: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    verb: str
    gerund: str
    danger: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    label: str
    phrase: str
    prep: str
    tail: str
    helps: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.problem_zone: set[str] = set()

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
        clone = World(self.setting)
        clone.entities = {k: replace(v, carries=set(v.carries), meters=dict(v.meters), memes=dict(v.memes))
                          for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.problem_zone = set(self.problem_zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _inc(d: dict[str, float], key: str, amount: float = 1.0) -> None:
    d[key] = d.get(key, 0.0) + amount


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "mesa": Setting(place="the red mesa road", tall=True, affords={"shuttle"}),
    "harbor": Setting(place="the harbor road", tall=True, affords={"shuttle"}),
    "canyon": Setting(place="the canyon pass", tall=True, affords={"shuttle"}),
}

PROBLEMS = {
    "blockade": Problem(
        id="blockade",
        verb="cross the blockade",
        gerund="crossing the blockade",
        danger="stuck and stalled",
        zone={"route"},
        keyword="blockade",
        tags={"blockade", "suspense"},
    ),
    "fog": Problem(
        id="fog",
        verb="find the landing line",
        gerund="floating through fog",
        danger="lost in the mist",
        zone={"route"},
        keyword="fog",
        tags={"fog", "suspense"},
    ),
}

SOLUTIONS = [
    Solution(
        id="signal",
        label="a bright signal lantern",
        phrase="a bright signal lantern",
        prep="light the signal lantern and ask for a way through",
        tail="lit the signal lantern and waited for the signal answer",
        helps={"blockade", "suspense"},
    ),
    Solution(
        id="detour",
        label="an old side path map",
        phrase="an old side path map",
        prep="take the old side path map and slip around the trouble",
        tail="followed the side path map around the trouble",
        helps={"blockade", "fog"},
    ),
    Solution(
        id="radio",
        label="a crackling radio",
        phrase="a crackling radio",
        prep="use the crackling radio to call for a safe opening",
        tail="used the crackling radio and heard a safe opening",
        helps={"blockade", "suspense"},
    ),
]

TALL_TALE_NAMES = ["Hank", "Mabel", "June", "Cyrus", "Annie", "Bo", "Nell", "Owen"]
TALL_TALE_TRAITS = ["steady", "brave", "mighty", "clever", "plucky", "wide-eyed"]


# ---------------------------------------------------------------------------
# Core simulation
# ---------------------------------------------------------------------------

def blockade_risk(problem: Problem) -> bool:
    return "route" in problem.zone


def compatible_solution(problem: Problem, solution: Solution) -> bool:
    return problem.id in solution.helps


def predict_stall(world: World, hero: Entity, problem: Problem) -> bool:
    sim = world.copy()
    _do_travel(sim, sim.get(hero.id), problem, narrate=False)
    shuttle = sim.get("shuttle")
    return shuttle.meters.get("stalled", 0.0) >= THRESHOLD


def _do_travel(world: World, hero: Entity, problem: Problem, narrate: bool = True) -> None:
    shuttle = world.get("shuttle")
    _inc(shuttle.meters, "distance", 1.0)
    if problem.id == "blockade":
        _inc(shuttle.meters, "stalled", 1.0)
        _inc(hero.memes, "suspense", 1.0)
        _inc(hero.memes, "worry", 1.0)
        if narrate:
            world.say(f"The shuttle rolled hard toward the blockade and then slowed to a worried crawl.")
    else:
        _inc(hero.meters, "travel", 1.0)
        if narrate:
            world.say(f"The shuttle kept on, singing against the wind.")


def tell_story(setting: Setting, problem: Problem, hero_name: str, hero_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    shuttle = world.add(Entity(id="shuttle", kind="thing", type="shuttle", label="shuttle", phrase="a little sky shuttle"))
    blockade = world.add(Entity(id="blockade", kind="thing", type="blockade", label="blockade", phrase="a blockade of wagons and ropes"))

    world.say(f"{hero.id} was a {trait} {hero.type} who loved to enjoy the long road in the sky.")
    world.say(f"Every day, {hero.id} watched the shuttle gleam and said {hero.pronoun('possessive')} plans were as big as a barn roof.")
    world.say(f"That was a tall-tailed kind of day, with {setting.place} stretching wide under the blue.")

    world.para()
    world.say(f"One day, {hero.id} climbed aboard the shuttle and looked ahead.")
    world.say(f"Then came the blockade, standing there like a row of stubborn teeth.")
    _inc(hero.memes, "inner_monologue", 1.0)
    world.say(f'“If I can’t get past that blockade,” {hero.id} thought, “I may have to sit here till sunset and count my own boots.”')
    if predict_stall(world, hero, problem):
        world.say(f"The thought made {hero.id}'s chest feel tight, because the shuttle would stall if nobody chose a clever path.")
    _do_travel(world, hero, problem, narrate=True)

    solution = next(s for s in SOLUTIONS if compatible_solution(problem, s))
    world.para()
    world.say(f"{hero.id} took a slow breath and peered through the trouble.")
    world.say(f'“I can still enjoy this ride,” {hero.id} told {hero.pronoun("object")}self, “if I use {solution.label}.”')
    _inc(hero.memes, "hope", 1.0)
    _inc(hero.memes, "resolve", 1.0)
    world.say(f"{hero.id} chose {solution.phrase}, because it was the kind of helper that could answer a blockade without a fuss.")
    world.say(f"Together, the plan and the shuttle {solution.tail}.")

    world.para()
    _inc(shuttle.meters, "speed", 1.0)
    shuttle.blocked_by = None
    _inc(hero.memes, "joy", 1.0)
    world.say(f"In the end, the shuttle slipped free at last.")
    world.say(f"{hero.id} laughed, the wind whooped, and the whole sky road seemed to enjoy the victory with {hero.pronoun('object')}.")
    world.say(f"The blockade was left behind like a grumpy fence in a story that had finally found its happy mile.")

    world.facts.update(
        hero=hero,
        shuttle=shuttle,
        blockade=blockade,
        problem=problem,
        solution=solution,
        setting=setting,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def prompts_for(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    problem = f["problem"]
    return [
        f'Write a Tall Tale for children about {hero.id}, a shuttle, and a {problem.keyword} blockade.',
        f"Tell a suspenseful but gentle story where {hero.id} wants to enjoy the ride, but a blockade stops the shuttle until a clever fix helps.",
        f'Write a child-friendly story that includes the words "enjoy", "blockade", and "shuttle", with a funny inner monologue and a big ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    problem = f["problem"]
    solution = f["solution"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do on the shuttle?",
            answer=f"{hero.id} wanted to enjoy the ride and keep going down the sky road.",
        ),
        QAItem(
            question=f"What got in the way of the shuttle?",
            answer=f"A {problem.keyword} blockade got in the way and made the trip feel suspenseful.",
        ),
        QAItem(
            question=f"What did {hero.id} think about when the shuttle slowed down?",
            answer=f"{hero.id} worried in an inner monologue about being stuck until sunset and counted boots in {hero.pronoun('possessive')} head.",
        ),
        QAItem(
            question=f"How did {hero.id} help the shuttle get past the trouble?",
            answer=f"{hero.id} used {solution.label} as a clever plan, and that helped the shuttle get free.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shuttle?",
            answer="A shuttle is a vehicle that carries people from one place to another, often on a set route.",
        ),
        QAItem(
            question="What is a blockade?",
            answer="A blockade is a barrier or blockage that keeps someone from going through easily.",
        ),
        QAItem(
            question="What does suspense mean in a story?",
            answer="Suspense is the feeling of wondering what will happen next when a problem is not fixed yet.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the secret talking someone does in their own mind while they think.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
problem_risk(P) :- problem(P), zone(P, route).
solution_ok(P, S) :- problem(P), solution(S), helps(S, P).
valid_story(Set, P, S) :- setting(Set), problem(P), solution(S), affords(Set, shuttle), problem_risk(P), solution_ok(P, S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for z in sorted(p.zone):
            lines.append(asp.fact("zone", pid, z))
    for sol in SOLUTIONS:
        lines.append(asp.fact("solution", sol.id))
        for p in sorted(sol.helps):
            lines.append(asp.fact("helps", sol.id, p))
    lines.append(asp.fact("vehicle", "shuttle"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(sid, pid, sol.id) for sid, s in SETTINGS.items() for pid, p in PROBLEMS.items()
          for sol in SOLUTIONS if "shuttle" in s.affords and blockade_risk(p) and compatible_solution(p, sol)}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} valid stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in ASP:", sorted(cl - py))
    print("only in Python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    problem: str
    name: str
    hero_type: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld about enjoy, blockade, and shuttle.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["boy", "girl", "captain", "navigator"])
    ap.add_argument("--trait", choices=TALL_TALE_TRAITS)
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
    place = args.place or rng.choice(list(SETTINGS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    name = args.name or rng.choice(TALL_TALE_NAMES)
    hero_type = args.hero_type or rng.choice(["boy", "girl", "captain", "navigator"])
    trait = args.trait or rng.choice(TALL_TALE_TRAITS)
    return StoryParams(place=place, problem=problem, name=name, hero_type=hero_type, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(SETTINGS[params.place], PROBLEMS[params.problem], params.name, params.hero_type, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts_for(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.blocked_by:
            bits.append(f"blocked_by={e.blocked_by}")
        lines.append(f"{e.id}: {', '.join(bits) if bits else 'empty'}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid stories")
        for item in stories:
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [
            generate(StoryParams(place="mesa", problem="blockade", name="Hank", hero_type="captain", trait="mighty")),
            generate(StoryParams(place="harbor", problem="blockade", name="Mabel", hero_type="navigator", trait="clever")),
            generate(StoryParams(place="canyon", problem="blockade", name="June", hero_type="girl", trait="plucky")),
        ]
    else:
        samples = []
        seen: set[str] = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            params.seed = base_seed + i
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
