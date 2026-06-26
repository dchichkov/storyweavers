#!/usr/bin/env python3
"""
storyworlds/worlds/underoos_problem_solving_adventure.py
=========================================================

A standalone story world for a small Adventure-style problem-solving tale
about underoos.

Premise:
- A child wants to head out on a brave little adventure.
- Their favorite underoos are missing, torn, or not ready.
- The child and helper search, test clues, and solve the problem with a
  sensible fix.

The story is constraint-driven: the problem must be real, the fix must
actually address it, and the ending must show the changed world state.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    danger: str
    clue: str
    fix: str
    action: str
    risk_region: str
    mess: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    label: str
    phrase: str
    covers: set[str]
    protects: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy

        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def join_two(a: str, b: str) -> str:
    return f"{a} and {b}"


def article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def describe_place(place: Place) -> str:
    if place.indoors:
        return f"The {place.label} was warm and bright, with shelves and corners to check."
    return f"The {place.label} was wide open, with paths, grass, and hiding places to search."


def wear_word(ent: Entity) -> str:
    return "them" if ent.plural else "it"


def problem_needs_fix(problem: Problem, solution: Solution) -> bool:
    return problem.risk_region in solution.covers and problem.id in solution.protects


def choose_solution(problem: Problem) -> Optional[Solution]:
    for sol in SOLUTIONS:
        if problem_needs_fix(problem, sol):
            return sol
    return None


def _r_find(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts["child"]
    problem = world.facts["problem"]
    if child.memes.get("searching", 0) < THRESHOLD:
        return out
    if world.facts.get("clue_found"):
        return out
    sig = ("clue", problem.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["clue_found"] = True
    child.memes["hope"] = child.memes.get("hope", 0) + 1
    out.append(
        f"After checking a few places, {child.id} found a clue: {problem.clue}."
    )
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts["child"]
    helper = world.facts["helper"]
    problem = world.facts["problem"]
    if not world.facts.get("clue_found"):
        return out
    sig = ("worry", problem.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["concern"] = helper.memes.get("concern", 0) + 1
    out.append(
        f"{helper.id} said the problem was real: if they rushed ahead, {problem.danger}."
    )
    child.memes["determination"] = child.memes.get("determination", 0) + 1
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts["child"]
    helper = world.facts["helper"]
    problem = world.facts["problem"]
    if not world.facts.get("clue_found"):
        return out
    if world.facts.get("resolved"):
        return out
    solution = choose_solution(problem)
    if solution is None:
        return out
    sig = ("fix", problem.id, solution.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item = world.add(
        Entity(
            id=solution.id,
            kind="thing",
            type="solution",
            label=solution.label,
            phrase=solution.phrase,
            owner=child.id,
            caretaker=helper.id,
            protective=True,
            plural=solution.plural,
        )
    )
    item.worn_by = child.id
    problem_state = child.meters.get(problem.mess, 0.0)
    if problem_state > 0:
        child.meters[problem.mess] = 0.0
    world.facts["resolved"] = True
    world.facts["solution"] = solution
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    helper.memes["pride"] = helper.memes.get("pride", 0) + 1
    out.append(
        f'Together they used {solution.label}; {solution.tail}.'
    )
    return out


CAUSAL_RULES = [_r_find, _r_worry, _r_fix]


def propagate(world: World) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    for s in out:
        world.say(s)
    return out


def adventure_intro(world: World, child: Entity, helper: Entity, problem: Problem) -> None:
    world.say(
        f"{child.id} was a brave little adventurer who loved big paths and tiny mysteries."
    )
    world.say(
        f"{child.pronoun().capitalize()} wanted to go on an adventure, but {child.pronoun('possessive')} favorite underoos were not ready."
    )
    world.say(
        f"{helper.id} looked around and said, \"Let's solve the problem first.\""
    )


def setup_problem(world: World, child: Entity, helper: Entity, problem: Problem) -> None:
    child.meters[problem.mess] = 1.0
    child.memes["searching"] = 1.0
    world.say(
        f"Then they noticed the trouble: {problem.label}."
    )
    world.say(describe_place(world.place))


def search_and_clue(world: World, child: Entity, helper: Entity, problem: Problem) -> None:
    world.say(
        f"{child.id} and {helper.id} searched under the bed, near the door, and behind the basket."
    )
    world.say(
        f"{child.id} asked, \"Could {problem.action} have happened here?\""
    )
    propagate(world)


def resolution(world: World, child: Entity, helper: Entity, problem: Problem) -> None:
    if not world.facts.get("resolved"):
        return
    solution = world.facts["solution"]
    child.memes["searching"] = 0.0
    world.say(
        f"{child.id} grinned and pulled on {solution.label} before the adventure."
    )
    world.say(
        f"At last, they could head out together, and the underoos stayed safe for the journey."
    )


PLACE_REGISTRY = {
    "bedroom": Place(id="bedroom", label="bedroom", indoors=True, affords={"search"}),
    "hall": Place(id="hall", label="hallway", indoors=True, affords={"search"}),
    "yard": Place(id="yard", label="yard", indoors=False, affords={"search"}),
    "treehouse": Place(id="treehouse", label="treehouse", indoors=False, affords={"search"}),
}

PROBLEMS = {
    "lost": Problem(
        id="lost",
        label="the underoos were missing",
        danger="the adventure would start late and the child would feel upset",
        clue="a tiny trail of fabric crumbs led behind the toy chest",
        fix="find the hidden underoos",
        action="hide them",
        risk_region="body",
        mess="searching",
        tags={"underoos", "lost", "search"},
    ),
    "muddy": Problem(
        id="muddy",
        label="the underoos were muddy",
        danger="mud would rub onto the rest of the outfit and make a mess",
        clue="one muddy footprint pointed straight to the wash basket",
        fix="wash and dry them",
        action="step in mud",
        risk_region="body",
        mess="muddy",
        tags={"underoos", "mud", "wash"},
    ),
    "torn": Problem(
        id="torn",
        label="the underoos had a small tear",
        danger="the tear could grow wider during the adventure",
        clue="a loose thread dangled from the seam",
        fix="patch the seam",
        action="catch on something",
        risk_region="body",
        mess="torn",
        tags={"underoos", "torn", "patch"},
    ),
    "wet": Problem(
        id="wet",
        label="the underoos were still damp",
        danger="damp cloth would feel cold and uncomfortable",
        clue="the clothesline held one sock that was still dripping",
        fix="wait for them to dry",
        action="get wet",
        risk_region="body",
        mess="wet",
        tags={"underoos", "wet", "dry"},
    ),
}

SOLUTIONS = [
    Solution(
        id="drawer_find",
        label="the spare underoos from the drawer",
        phrase="a clean backup pair",
        covers={"body"},
        protects={"lost"},
        prep="look in the drawer for a backup pair",
        tail="found the spare underoos in the drawer",
    ),
    Solution(
        id="wash_and_spin",
        label="the washing line and a warm spin in the dryer",
        phrase="a drying plan",
        covers={"body"},
        protects={"wet"},
        prep="hang them up and wait",
        tail="gave the underoos time to dry",
    ),
    Solution(
        id="patch_kit",
        label="the patch kit",
        phrase="a tiny repair kit",
        covers={"body"},
        protects={"torn"},
        prep="use the patch kit carefully",
        tail="patched the seam so the tear would not grow",
    ),
    Solution(
        id="scrub_basket",
        label="the soap and scrub basket",
        phrase="a wash-and-rinse plan",
        covers={"body"},
        protects={"muddy"},
        prep="wash them clean",
        tail="washed the mud away and hung them up",
    ),
]


NAMES = ["Milo", "Nina", "Ari", "Pia", "Theo", "Juno", "Bea", "Otis"]
HELPERS = ["Mom", "Dad", "Auntie", "Grandpa", "Big Sister", "Big Brother"]
TRAITS = ["brave", "curious", "patient", "spirited", "clever"]


@dataclass
class StoryParams:
    place: str
    problem: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in PLACE_REGISTRY:
        for prob in PROBLEMS:
            if choose_solution(PROBLEMS[prob]) is not None:
                combos.append((place, prob))
    return combos


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    problem = world.facts["problem"]
    return [
        f'Write an adventure story for a young child named {child.id} about underoos and a problem that can be solved.',
        f"Tell a story where {child.id} and {helper.id} notice that {problem.label} and then work together to fix it.",
        f"Write a short, child-friendly adventure with a clue, a fix, and a happy ending involving underoos.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    problem = world.facts["problem"]
    solution = world.facts.get("solution")
    qa = [
        QAItem(
            question=f"What adventure did {child.id} want to go on before they solved the problem?",
            answer=f"{child.id} wanted to go on an adventure, but {child.pronoun('possessive')} underoos were not ready yet.",
        ),
        QAItem(
            question=f"What was the problem with the underoos?",
            answer=f"The problem was that {problem.label}.",
        ),
        QAItem(
            question=f"How did {child.id} and {helper.id} work together?",
            answer=f"They searched for a clue, found the problem, and then chose a sensible fix.",
        ),
    ]
    if solution:
        qa.append(
            QAItem(
                question=f"What helped solve the underoos problem?",
                answer=f"{solution.label} helped because it matched the problem and let {child.id} get ready safely.",
            )
        )
        qa.append(
            QAItem(
                question=f"What happened at the end of the story?",
                answer=f"{child.id} put on {solution.label} and the adventure could begin with the problem solved.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What are underoos?",
            answer="Underoos are underwear or superhero-style underwear that a child wears under clothes.",
        ),
        QAItem(
            question="Why do people fix torn clothes?",
            answer="People fix torn clothes so the tear does not get bigger and the clothes can be worn safely again.",
        ),
        QAItem(
            question="Why is it important to dry wet clothes?",
            answer="Wet clothes need to dry so they feel comfortable and do not make the wearer cold.",
        ),
    ]
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append("protective=True")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:14} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
problem_needs_fix(P,S) :- problem(P), solution(S), risk_region(P,R), covers(S,R), protects(S,P).
valid(P,Prob) :- place(P), problem(Prob), problem_needs_fix(Prob,_).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACE_REGISTRY.items():
        lines.append(asp.fact("place", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for prob_id, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", prob_id))
        lines.append(asp.fact("risk_region", prob_id, prob.risk_region))
        lines.append(asp.fact("mess", prob_id, prob.mess))
        for tag in sorted(prob.tags):
            lines.append(asp.fact("tag", prob_id, tag))
    for sol in SOLUTIONS:
        lines.append(asp.fact("solution", sol.id))
        for c in sorted(sol.covers):
            lines.append(asp.fact("covers", sol.id, c))
        for p in sorted(sol.protects):
            lines.append(asp.fact("protects", sol.id, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in clingo:", sorted(a - b))
    print(" only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world about solving an underoos problem.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.problem and PROBLEMS[args.problem].id not in PROBLEMS:
        raise StoryError("Unknown problem.")
    if args.place and args.problem:
        if (args.place, args.problem) not in combos:
            raise StoryError("No valid story matches those explicit choices.")
    filtered = [c for c in combos if (args.place is None or c[0] == args.place) and (args.problem is None or c[1] == args.problem)]
    if not filtered:
        raise StoryError("No valid combination matches the given options.")
    place, prob = rng.choice(sorted(filtered))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, problem=prob, name=name, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = World(PLACE_REGISTRY[params.place])
    child = world.add(Entity(id=params.name, kind="character", type="boy" if params.name in {"Milo", "Theo", "Otis", "Ari"} else "girl"))
    helper = world.add(Entity(id=params.helper, kind="character", type="adult"))
    problem = PROBLEMS[params.problem]
    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["problem"] = problem

    adventure_intro(world, child, helper, problem)
    world.para()
    setup_problem(world, child, helper, problem)
    search_and_clue(world, child, helper, problem)
    world.para()
    resolution(world, child, helper, problem)

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


CURATED = [
    StoryParams(place="bedroom", problem="lost", name="Milo", helper="Mom", trait="curious"),
    StoryParams(place="yard", problem="wet", name="Nina", helper="Dad", trait="brave"),
    StoryParams(place="hall", problem="torn", name="Ari", helper="Auntie", trait="patient"),
    StoryParams(place="treehouse", problem="muddy", name="Juno", helper="Big Sister", trait="spirited"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, problem) combos:\n")
        for place, prob in combos:
            print(f"  {place:10} {prob}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.problem} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
