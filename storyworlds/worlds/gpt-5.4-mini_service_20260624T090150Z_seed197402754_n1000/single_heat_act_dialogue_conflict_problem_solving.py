#!/usr/bin/env python3
"""
storyworlds/worlds/single_heat_act_dialogue_conflict_problem_solving.py
======================================================================

A small slice-of-life story world about one person on a hot day, a small act,
a spoken disagreement, and a practical fix.

Premise:
- A single character wants to do one simple act in the heat.
- Another person worries because the heat makes the act uncomfortable or risky.
- They talk it through, hit a little conflict, then solve the problem together.

The world is intentionally tiny and constraint-checked:
- the chosen act must plausibly be affected by heat
- the suggested fix must actually address the problem
- the ending must show a state change, not just a moral
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "person"
    type: str = "person"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    indoor: bool
    affords: set[str]


@dataclass
class Act:
    id: str
    verb: str
    gerund: str
    rush: str
    heat_risk: str
    effect: str
    setting_note: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    symptom: str
    cause: str
    fix_label: str
    fix_action: str
    solves: set[str]


@dataclass
class Solution:
    id: str
    label: str
    prep: str
    tail: str
    solves: set[str]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.weather = "hot"

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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.weather = self.weather
        return w


SETTINGS = {
    "balcony": Place("balcony", "the balcony", False, {"sit", "draw", "sip"}),
    "kitchen": Place("kitchen", "the kitchen", True, {"bake", "draw", "sip"}),
    "porch": Place("porch", "the porch", False, {"sit", "draw", "sip"}),
    "library_corner": Place("library_corner", "the library corner", True, {"read", "draw", "sip"}),
}

ACTS = {
    "draw": Act(
        id="draw",
        verb="draw pictures",
        gerund="drawing pictures",
        rush="run to the table with crayons",
        heat_risk="the crayons could get too soft",
        effect="the colors smeared and bent",
        setting_note="The air felt still and warm.",
        keyword="draw",
        tags={"art", "heat"},
    ),
    "sip": Act(
        id="sip",
        verb="sip a cold drink",
        gerund="sipping a cold drink",
        rush="grab the cup too fast",
        heat_risk="the ice could melt too quickly",
        effect="the drink turned warm",
        setting_note="The day felt sticky and bright.",
        keyword="sip",
        tags={"drink", "heat"},
    ),
    "read": Act(
        id="read",
        verb="read a book",
        gerund="reading a book",
        rush="flop into the chair with the book",
        heat_risk="the room felt too heavy to settle down",
        effect="their attention drifted",
        setting_note="Even the quiet place felt warm.",
        keyword="read",
        tags={"quiet", "heat"},
    ),
    "bake": Act(
        id="bake",
        verb="bake small cookies",
        gerund="baking small cookies",
        rush="open the oven too soon",
        heat_risk="the kitchen already felt extra hot",
        effect="the room grew uncomfortably warm",
        setting_note="The kitchen held the heat like a little blanket.",
        keyword="bake",
        tags={"food", "heat"},
    ),
}

PROBLEMS = {
    "melt": Problem(
        id="melt",
        label="melted crayons",
        symptom="the crayons would get too soft",
        cause="heat",
        fix_label="move to a cooler spot",
        fix_action="cool",
        solves={"draw"},
    ),
    "warm_drink": Problem(
        id="warm_drink",
        label="warm drink",
        symptom="the ice would melt too fast",
        cause="heat",
        fix_label="add more ice and a shaded seat",
        fix_action="shade",
        solves={"sip"},
    ),
    "sticky_room": Problem(
        id="sticky_room",
        label="sticky room",
        symptom="it felt too hard to settle down",
        cause="heat",
        fix_label="open a fan and read by the window",
        fix_action="fan",
        solves={"read"},
    ),
    "hot_kitchen": Problem(
        id="hot_kitchen",
        label="hot kitchen",
        symptom="the kitchen felt too warm already",
        cause="heat",
        fix_label="wait for a cooler time and use a fan",
        fix_action="wait",
        solves={"bake"},
    ),
}

SOLUTIONS = {
    "shade": Solution(
        id="shade",
        label="the shady chair and a fresh cup with more ice",
        prep="move to the shady chair and add more ice",
        tail="moved to the shady chair and the drink stayed cool",
        solves={"warm_drink"},
    ),
    "cool": Solution(
        id="cool",
        label="the cool table near the open window",
        prep="move to the cool table near the open window",
        tail="moved to the cool table and the crayons stayed firm",
        solves={"melt"},
    ),
    "fan": Solution(
        id="fan",
        label="the fan near the window",
        prep="turn on the fan and sit by the window",
        tail="turned on the fan and the room felt easier",
        solves={"sticky_room"},
    ),
    "wait": Solution(
        id="wait",
        label="a later time after the sun cooled down",
        prep="wait for later and open a window",
        tail="waited a little and the kitchen felt kinder",
        solves={"hot_kitchen"},
    ),
}

NAMES = ["Mina", "Jules", "Noah", "Iris", "Leo", "Nia", "Owen", "Maya"]
KINDS = ["girl", "boy"]
PARENTS = ["mother", "father", "neighbor", "aunt"]
TRAITS = ["quiet", "gentle", "curious", "careful", "spirited", "patient"]


def compatible(place: Place, act: Act, problem: Problem, solution: Solution) -> bool:
    return act.id in place.affords and act.id in problem.solves and problem.id in solution.solves


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for pid, place in SETTINGS.items():
        for aid, act in ACTS.items():
            for prob_id, prob in PROBLEMS.items():
                for sol_id, sol in SOLUTIONS.items():
                    if compatible(place, act, prob, sol):
                        combos.append((pid, aid, prob_id, sol_id))
    return combos


@dataclass
class StoryParams:
    place: str
    act: str
    problem: str
    solution: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life heat / act / dialogue / conflict / problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--act", choices=ACTS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--gender", choices=KINDS)
    ap.add_argument("--parent", choices=PARENTS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.act is None or c[1] == args.act)
              and (args.problem is None or c[2] == args.problem)
              and (args.solution is None or c[3] == args.solution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, act, prob, sol = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(KINDS)
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENTS)
    trait = rng.choice(TRAITS)
    return StoryParams(place, act, prob, sol, name, gender, parent, trait)


def _setup(world: World, params: StoryParams) -> tuple[Entity, Entity, Act, Problem, Solution]:
    hero = world.add(Entity(params.name, kind="person", type=params.gender))
    other = world.add(Entity("Other", kind="person", type=params.parent, label=params.parent))
    act = ACTS[params.act]
    prob = PROBLEMS[params.problem]
    sol = SOLUTIONS[params.solution]
    world.facts.update(hero=hero, other=other, act=act, prob=prob, sol=sol, params=params)
    return hero, other, act, prob, sol


def _do_act(world: World, hero: Entity, act: Act) -> None:
    hero.meters.setdefault("heat", 0.0)
    hero.metes = hero.meters  # harmless alias if inspected in trace
    hero.memes.setdefault("want", 0.0)
    hero.memes["want"] += 1
    world.say(f"{hero.id} was a {world.facts['params'].trait} {hero.type} on {world.place.label}.")
    world.say(f"{act.setting_note} {hero.id} wanted to {act.verb}, because {act.gerund} felt nice.")
    hero.meters["heat"] += 1
    world.facts["act_started"] = True


def _predict_problem(act: Act, prob: Problem) -> bool:
    return act.id in prob.solves


def _warn(world: World, other: Entity, hero: Entity, act: Act, prob: Problem) -> bool:
    if not _predict_problem(act, prob):
        return False
    world.say(f'"If you do that, {prob.symptom}," {other.pronoun("subject")} said.')
    world.say(f'"{act.effect} would be no fun," {other.pronoun("subject")} added.')
    hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1
    world.facts["warned"] = True
    return True


def _reply(world: World, hero: Entity, other: Entity, act: Act) -> None:
    world.say(f'"But I really want to {act.verb}," {hero.pronoun("subject")} said.')
    world.say(f'"I know," {other.pronoun("subject")} said, "and we can still find a better way."')
    hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1
    world.facts["dialogue"] = True


def _solve(world: World, hero: Entity, other: Entity, act: Act, prob: Problem, sol: Solution) -> None:
    if act.id not in prob.solves or prob.id not in sol.solves:
        return
    world.para()
    world.say(f'{other.pronoun("subject").capitalize()} looked around and said, "How about we {sol.prep}?"')
    world.say(f'{hero.pronoun("subject").capitalize()} nodded. "Okay," {hero.pronoun("subject")} said. "That sounds better."')
    hero.memes["conflict"] = 0.0
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    hero.meters["heat"] = max(0.0, hero.meters.get("heat", 0.0) - 1)
    world.facts["solved"] = True
    world.say(f"They {sol.tail}, and {hero.id} got back to {act.gerund} with a calmer smile.")


def tell(params: StoryParams) -> World:
    place = SETTINGS[params.place]
    world = World(place)
    hero, other, act, prob, sol = _setup(world, params)
    _do_act(world, hero, act)
    world.para()
    _warn(world, other, hero, act, prob)
    _reply(world, hero, other, act)
    _solve(world, hero, other, act, prob, sol)
    world.facts["ended_calm"] = hero.memes.get("conflict", 0.0) == 0.0
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    act = world.facts["act"]
    prob = world.facts["prob"]
    return [
        f'Write a slice-of-life story about a single child who wants to {act.verb} in the heat.',
        f"Tell a gentle story where {p.name} and {p.parent} talk through a small problem and find a practical fix.",
        f'Write a short story that includes the word "{act.keyword}" and ends with a calm solution to the heat problem.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    hero: Entity = world.facts["hero"]
    other: Entity = world.facts["other"]
    act: Act = world.facts["act"]
    prob: Problem = world.facts["prob"]
    sol: Solution = world.facts["sol"]
    return [
        QAItem(
            question=f"What did {p.name} want to do on the hot day?",
            answer=f"{p.name} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did {other.label} worry about it?",
            answer=f"{other.label.capitalize()} worried because {prob.symptom}, and the heat made the problem worse.",
        ),
        QAItem(
            question=f"How did they solve the problem?",
            answer=f"They solved it by using {sol.label}, so {p.name} could keep going without the heat getting in the way.",
        ),
        QAItem(
            question=f"How did {p.name} feel at the end?",
            answer=f"{p.name} felt calmer and happier after the solution, and the little conflict was gone.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does heat often do to people on a summer day?",
               answer="Heat can make people feel sticky, tired, or uncomfortable, so they often look for shade, water, or a cooler spot."),
        QAItem(question="Why is it helpful to talk when two people want different things?",
               answer="Talking helps people explain their feelings and find a plan that works for both of them."),
        QAItem(question="What is problem solving?",
               answer="Problem solving means noticing what is wrong and choosing a good way to fix it."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
act(heat_action) :- action(draw); action(sip); action(read); action(bake).

problem(P) :- problem_id(P).
solution(S) :- solution_id(S).

compatible(Place, Act, Prob, Sol) :-
    affords(Place, Act),
    solves_problem(Prob, Act),
    solves_solution(Sol, Prob).

valid_story(Place, Act, Prob, Sol) :-
    place(Place), action(Act), problem_id(Prob), solution_id(Sol),
    compatible(Place, Act, Prob, Sol).

#show valid_story/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if p.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTS:
        lines.append(asp.fact("action", aid))
    for prob_id, prob in PROBLEMS.items():
        lines.append(asp.fact("problem_id", prob_id))
        for a in sorted(prob.solves):
            lines.append(asp.fact("solves_problem", prob_id, a))
    for sol_id, sol in SOLUTIONS.items():
        lines.append(asp.fact("solution_id", sol_id))
        for p in sorted(sol.solves):
            lines.append(asp.fact("solves_solution", sol_id, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def explain_rejection(act: Act, prob: Problem) -> str:
    return f"(No story: {act.verb} does not match the heat problem '{prob.label}' in a way the solution catalog can honestly fix.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.act and args.problem:
        if not compatible(SETTINGS[args.place] if args.place else list(SETTINGS.values())[0], ACTS[args.act], PROBLEMS[args.problem], SOLUTIONS[args.solution] if args.solution else list(SOLUTIONS.values())[0]):
            pass
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.act is None or c[1] == args.act)
              and (args.problem is None or c[2] == args.problem)
              and (args.solution is None or c[3] == args.solution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, act, prob, sol = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(KINDS)
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENTS)
    trait = rng.choice(TRAITS)
    return StoryParams(place, act, prob, sol, name, gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [c for c in valid_combos.__wrapped__()]  # type: ignore[attr-defined]


def _valid_combos_impl() -> list[tuple[str, str, str, str]]:
    return [
        (pid, aid, prob_id, sol_id)
        for pid, place in SETTINGS.items()
        for aid, act in ACTS.items()
        if aid in place.affords
        for prob_id, prob in PROBLEMS.items()
        if aid in prob.solves
        for sol_id, sol in SOLUTIONS.items()
        if prob_id in sol.solves
    ]


valid_combos.__wrapped__ = _valid_combos_impl  # type: ignore[attr-defined]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible story combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(StoryParams(*c, name="Mina", gender="girl", parent="mother", trait="patient")) for c in valid_combos()[:5]]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
