#!/usr/bin/env python3
"""
storyworlds/worlds/scholar_alliance_picnic_meadow_problem_solving_humor.py
==========================================================================

A small animal-story world set in a picnic meadow.

Seed premise:
- A scholar animal plans a picnic in a meadow.
- An alliance of animals faces a practical problem at the picnic.
- Humor helps them stay calm while they solve it.
- Reconciliation ends the story with a kinder shared plan.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "owl": {"subject": "he", "object": "him", "possessive": "his"},
            "fox": {"subject": "he", "object": "him", "possessive": "his"},
            "rabbit": {"subject": "she", "object": "her", "possessive": "her"},
            "mouse": {"subject": "she", "object": "her", "possessive": "her"},
            "badger": {"subject": "they", "object": "them", "possessive": "their"},
            "squirrel": {"subject": "they", "object": "them", "possessive": "their"},
            "duck": {"subject": "she", "object": "her", "possessive": "her"},
        }
        d = mapping.get(self.type, {"subject": "it", "object": "it", "possessive": "its"})
        return d[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Meadow:
    place: str = "the picnic meadow"
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    noun: str
    verb: str
    mess: str
    zone: set[str]
    hint: str


@dataclass
class Solution:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str]
    covers: set[str]
    plural: bool = False


class World:
    def __init__(self, meadow: Meadow) -> None:
        self.meadow = meadow
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.problem_zone: set[str] = set()

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

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.meadow)
        c.entities = copy.deepcopy(self.entities)
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        c.problem_zone = set(self.problem_zone)
        c.paragraphs = [[]]
        return c


PROBLEMS = {
    "wind": Problem(
        id="wind",
        noun="wind",
        verb="blew",
        mess="scattered",
        zone={"blanket", "basket"},
        hint="a gust that can scatter food and napkins",
    ),
    "ants": Problem(
        id="ants",
        noun="ants",
        verb="marched",
        mess="crowded",
        zone={"basket", "cake"},
        hint="tiny insects that march toward sweet food",
    ),
    "rain": Problem(
        id="rain",
        noun="rain",
        verb="dripped",
        mess="wet",
        zone={"blanket", "cake"},
        hint="water that falls from clouds and can spoil a picnic",
    ),
    "mud": Problem(
        id="mud",
        noun="mud",
        verb="splashed",
        mess="muddy",
        zone={"paws", "blanket"},
        hint="soft wet dirt that sticks to feet and cloth",
    ),
}

SOLUTIONS = [
    Solution(
        id="stone-pins",
        label="stone pins",
        prep="pin down the blanket with stone pins",
        tail="pinned the blanket down with stone pins",
        guards={"scattered"},
        covers={"blanket"},
        plural=True,
    ),
    Solution(
        id="lid-basket",
        label="a lid for the basket",
        prep="cover the basket with a snug lid",
        tail="covered the basket with a snug lid",
        guards={"crowded"},
        covers={"basket"},
    ),
    Solution(
        id="leaf-hood",
        label="a leaf hood",
        prep="hold up a broad leaf hood",
        tail="held up the leaf hood",
        guards={"wet"},
        covers={"cake"},
    ),
    Solution(
        id="bridge-stones",
        label="a line of bridge stones",
        prep="place bridge stones by the muddy path",
        tail="placed bridge stones by the muddy path",
        guards={"muddy"},
        covers={"paws"},
        plural=True,
    ),
]

ANIMALS = [
    ("Olin", "owl"),
    ("Fenna", "fox"),
    ("Bibi", "rabbit"),
    ("Milo", "mouse"),
    ("Grove", "badger"),
    ("Pip", "squirrel"),
    ("Della", "duck"),
]

TRAITS = ["curious", "gentle", "serious", "bright-eyed", "patient", "witty"]


def reasonableness(problem: Problem, solution: Solution) -> bool:
    return problem.mess in solution.guards and bool(problem.zone & solution.covers)


def select_solution(problem: Problem) -> Optional[Solution]:
    for s in SOLUTIONS:
        if reasonableness(problem, s):
            return s
    return None


def predict_damage(world: World, hero: Entity, problem: Problem, item_id: str) -> bool:
    sim = world.copy()
    _do_problem(sim, sim.get(hero.id), problem, narrate=False)
    item = sim.entities[item_id]
    return item.meters.get(problem.mess, 0.0) >= THRESHOLD


def _do_problem(world: World, hero: Entity, problem: Problem, narrate: bool = True) -> list[str]:
    out: list[str] = []
    world.problem_zone = set(problem.zone)
    hero.meters[problem.mess] = hero.meters.get(problem.mess, 0.0) + 1
    hero.memes["trouble"] = hero.memes.get("trouble", 0.0) + 1
    for item in world.entities.values():
        if item.kind != "thing" or item.worn_by != hero.id:
            continue
        if problem.zone.isdisjoint({"blanket", "basket", "cake", "paws"}) and problem.mess not in {"wet", "muddy"}:
            continue
        if item.id == "basket" and "basket" in problem.zone:
            item.meters[problem.mess] = item.meters.get(problem.mess, 0.0) + 1
        if item.id == "blanket" and "blanket" in problem.zone:
            item.meters[problem.mess] = item.meters.get(problem.mess, 0.0) + 1
        if item.id == "cake" and "cake" in problem.zone:
            item.meters[problem.mess] = item.meters.get(problem.mess, 0.0) + 1
        if item.id == "paws" and "paws" in problem.zone:
            item.meters[problem.mess] = item.meters.get(problem.mess, 0.0) + 1
        if item.meters.get(problem.mess, 0.0) >= THRESHOLD:
            out.append(f"{item.name_or_label().capitalize()} got {problem.mess}.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def setup_story(world: World, hero: Entity, ally: Entity, problem: Problem, picnic: Entity, blanket: Entity, basket: Entity, cake: Entity) -> None:
    world.say(f"{hero.name_or_label()} was a little {hero.type} scholar who loved quiet questions and careful notes.")
    world.say(f"{hero.pronoun().capitalize()} and {ally.name_or_label()} were part of a small alliance that liked sharing good ideas.")
    world.say(f"One bright day, they planned a picnic in {world.meadow.place} with a blanket, a basket, and a cake.")
    world.say(f"{hero.name_or_label()} had written a page about {problem.hint}, and everyone wanted the picnic to go well.")
    picnic.worn_by = hero.id
    blanket.worn_by = hero.id
    basket.worn_by = hero.id
    cake.worn_by = hero.id


def start_problem(world: World, hero: Entity, ally: Entity, problem: Problem) -> None:
    world.para()
    world.say(f"Then {problem.noun} showed up at the picnic.")
    world.say(f"It {problem.verb} in from the edge of the meadow and tried to make everything messy.")
    world.say(f"{hero.name_or_label()} frowned, but {ally.name_or_label()} gave a funny little shrug that made the others blink and smile.")
    world.say(f"{hero.pronoun().capitalize()} said they should solve it together instead of arguing.")


def solve_problem(world: World, hero: Entity, ally: Entity, problem: Problem, item: Entity) -> Optional[Solution]:
    sol = select_solution(problem)
    if sol is None:
        return None
    if predict_damage(world, hero, problem, item.id):
        world.say(f"{hero.name_or_label()} studied the picnic and noticed the trouble could be handled with a simple tool.")
        world.say(f"{ally.name_or_label()} joked that even a squirrel could see the answer once the hint was written down plainly.")
        world.say(f"So they chose to {sol.prep}.")
        item.worn_by = hero.id
        return sol
    return None


def reconcile(world: World, hero: Entity, ally: Entity, problem: Problem, sol: Solution, picnic: Entity, blanket: Entity, basket: Entity, cake: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1
    ally.memes["peace"] = ally.memes.get("peace", 0.0) + 1
    world.say(f"{hero.name_or_label()} and {ally.name_or_label()} laughed together when the fix worked.")
    world.say(f"After that, the alliance felt stronger, because everyone had helped, and nobody had to stay cross.")
    world.say(f"They {sol.tail}, and the picnic stayed neat enough for eating.")
    world.say(f"At the end, {hero.name_or_label()} shared the cake, {ally.name_or_label()} shared the jokes, and the meadow felt friendly again.")


def tell_story(params_seed: int = 0, problem_id: Optional[str] = None) -> World:
    rng = random.Random(params_seed)
    meadow = Meadow(place="the picnic meadow", affords=set(PROBLEMS))
    world = World(meadow)

    hero_name, hero_type = rng.choice(ANIMALS)
    ally_name, ally_type = rng.choice([a for a in ANIMALS if a[0] != hero_name])

    problem = PROBLEMS[problem_id or rng.choice(list(PROBLEMS))]
    if problem_id and problem_id not in PROBLEMS:
        raise StoryError("Unknown problem.")
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    ally = world.add(Entity(id=ally_name, kind="character", type=ally_type))
    picnic = world.add(Entity(id="picnic", type="thing", label="picnic", phrase="the picnic spread"))
    blanket = world.add(Entity(id="blanket", type="thing", label="blanket", phrase="the picnic blanket"))
    basket = world.add(Entity(id="basket", type="thing", label="basket", phrase="the food basket"))
    cake = world.add(Entity(id="cake", type="thing", label="cake", phrase="the cake"))

    setup_story(world, hero, ally, problem, picnic, blanket, basket, cake)
    start_problem(world, hero, ally, problem)
    sol = solve_problem(world, hero, ally, problem, blanket) or select_solution(problem)
    if sol is None:
        raise StoryError("No reasonable solution exists for this problem.")
    world.para()
    world.say(f"{ally.name_or_label()} pointed to the right fix: {sol.label}.")
    world.say(f"{hero.name_or_label()} nodded, because the answer was sensible and kind.")
    reconcile(world, hero, ally, problem, sol, picnic, blanket, basket, cake)

    world.facts.update(
        hero=hero,
        ally=ally,
        problem=problem,
        solution=sol,
        picnic=picnic,
        blanket=blanket,
        basket=basket,
        cake=cake,
    )
    return world


@dataclass
class StoryParams:
    problem: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(problem="wind"),
    StoryParams(problem="ants"),
    StoryParams(problem="rain"),
    StoryParams(problem="mud"),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    ally = f["ally"]
    problem = f["problem"]
    return [
        f"Write a short animal story set in the picnic meadow about a scholar named {hero.name_or_label()} and an alliance of friends.",
        f"Tell a gentle story where {hero.name_or_label()} and {ally.name_or_label()} face {problem.noun} at a picnic and solve it together with humor.",
        f"Write a child-friendly tale about a picnic meadow, a practical problem, and reconciliation after a smart fix is found.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    ally = f["ally"]
    problem = f["problem"]
    sol = f["solution"]
    return [
        QAItem(
            question=f"Who was the scholar in the story?",
            answer=f"{hero.name_or_label()} was the little {hero.type} scholar who loved careful thinking.",
        ),
        QAItem(
            question=f"What kind of place was the picnic held in?",
            answer=f"The picnic was held in {world.meadow.place}.",
        ),
        QAItem(
            question=f"What problem did the alliance need to solve?",
            answer=f"They needed to deal with {problem.noun}, which could make the picnic messy.",
        ),
        QAItem(
            question=f"How did {hero.name_or_label()} and {ally.name_or_label()} feel by the end?",
            answer=f"They felt happy and reconciled after they solved the problem together.",
        ),
        QAItem(
            question=f"What simple fix did they choose?",
            answer=f"They chose {sol.label} as the practical way to handle the trouble.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    problem = f["problem"]
    return [
        QAItem(
            question="What is a scholar?",
            answer="A scholar is a person or character who likes learning, reading, and thinking carefully about ideas.",
        ),
        QAItem(
            question="What does an alliance mean?",
            answer="An alliance is a group of friends who agree to work together for a shared goal.",
        ),
        QAItem(
            question="Why can wind be a picnic problem?",
            answer="Wind can blow light things around, so napkins, crumbs, and blankets can get scattered.",
        ),
        QAItem(
            question="Why is humor helpful when solving a problem?",
            answer="Humor can help everyone stay calm and friendly while they look for a good answer.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop feeling upset and become friendly again.",
        ),
        QAItem(
            question=f"What do {problem.noun} or similar troubles often need in a picnic story?",
            answer="They often need a practical fix, like covering, pinning, or moving something safely.",
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
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  problem_zone: {sorted(world.problem_zone)}")
    return "\n".join(lines)


ASP_RULES = r"""
problem_at_risk(P, Z) :- problem(P), zone(P, Z).
solution_fits(S, P) :- solution(S), problem(P), guards(S, M), problem_mess(P, M), covers(S, Z), zone(P, Z).
valid_story(P, S) :- problem(P), solution_fits(S, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("problem_mess", pid, p.mess))
        for z in sorted(p.zone):
            lines.append(asp.fact("zone", pid, z))
    for s in SOLUTIONS:
        lines.append(asp.fact("solution", s.id))
        for g in sorted(s.guards):
            lines.append(asp.fact("guards", s.id, g))
        for c in sorted(s.covers):
            lines.append(asp.fact("covers", s.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for pid, p in PROBLEMS.items():
        for s in SOLUTIONS:
            if reasonableness(p, s):
                out.append((pid, s.id))
    return out


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: a scholar, an alliance, a picnic meadow, and a fix."
    )
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
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
    problem = args.problem or rng.choice(sorted(PROBLEMS))
    if problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    return StoryParams(problem=problem)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params.seed or 0, params.problem)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible problem/solution pairs:\n")
        for p, s in combos:
            print(f"  {p:8} {s}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(StoryParams(problem=p.problem, seed=base_seed + i)) for i, p in enumerate(CURATED)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
