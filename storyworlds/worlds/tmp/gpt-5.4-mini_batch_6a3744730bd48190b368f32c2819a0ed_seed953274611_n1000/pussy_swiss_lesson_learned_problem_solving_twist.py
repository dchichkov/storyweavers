#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pussy_swiss_lesson_learned_problem_solving_twist.py
====================================================================================

A tiny, tall-tale storyworld about a barn cat called Pussy, a block of Swiss
cheese, a problem to solve, and a twist that teaches a lesson.

The domain is built to satisfy the shared Storyweavers contract:
- self-contained stdlib script
- StoryParams, build_parser, resolve_params, generate, emit, main
- stateful simulation with meters and memes
- reasonableness gate and inline ASP twin
- prompts, story-grounded QA, and world-knowledge QA
- --verify smoke-tests generation and checks Python/ASP parity
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict[str, Any] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"fullness": 0.0, "stuck": 0.0, "helped": 0.0, "safe": 0.0}
        if not self.memes:
            self.memes = {"pride": 0.0, "worry": 0.0, "relief": 0.0, "joy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cat"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"farmer", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Problem:
    id: str
    label: str
    place: str
    needs: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    label: str
    tool: str
    method: str
    effect: str
    followup: str
    power: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Twist:
    id: str
    reveal: str
    turn: str
    lesson: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple[Any, ...]] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, Any] = {}

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: callable


def _r_fill(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.role != "cat":
            continue
        if e.meters["fullness"] < THRESHOLD:
            continue
        sig = ("fill", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["pride"] += 1
        out.append("__full__")
    return out


def _r_help(world: World) -> list[str]:
    out = []
    if world.facts.get("helped"):
        sig = ("help",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("cat").meters["helped"] += 1
            out.append("__help__")
    return out


CAUSAL_RULES = [Rule("fill", _r_fill), Rule("help", _r_help)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
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


def smell_reasonable(problem: Problem, solution: Solution, twist: Twist) -> bool:
    return problem.id in PROBLEMS and solution.id in SOLUTIONS and twist.id in TWISTS


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, s, t) for p in PROBLEMS for s in SOLUTIONS for t in TWISTS
            if smell_reasonable(PROBLEMS[p], SOLUTIONS[s], TWISTS[t])]


def best_solution() -> Solution:
    return max(SOLUTIONS.values(), key=lambda s: s.power)


def predict(world: World, problem: Problem) -> dict[str, Any]:
    sim = world.copy()
    sim.get("cat").meters["fullness"] += 1
    sim.get("cat").meters["stuck"] += 1
    return {"stuck": sim.get("cat").meters["stuck"] >= THRESHOLD}


def open_scene(world: World, cat: Entity, farmer: Entity, problem: Problem) -> None:
    cat.memes["joy"] += 1
    world.say(
        f"In the wide old barn, Pussy the cat strutted across the hay like she "
        f"owned the moon. The {problem.place} had gone quiet, and the little "
        f"{problem.label} problem was bigger than a fence-post in a flood."
    )
    world.say(
        f"{farmer.id} scratched his head and said the pantry was short on {problem.needs}."
    )


def describe_need(world: World, cat: Entity, problem: Problem) -> None:
    world.say(
        f"Pussy sniffed the air and declared, \"A barn runs on clever feet and a "
        f"full belly, and right now this one needs {problem.needs}.\""
    )
    world.say(
        f"She tipped her whiskers at the {problem.place}, where the trouble was hiding."
    )


def attempt(world: World, cat: Entity, solution: Solution, problem: Problem) -> None:
    cat.memes["pride"] += 1
    world.say(
        f'\"I can fix it,\" Pussy said, and she went to work with a tail-swish and '
        f'a grand idea: {solution.method}.'
    )


def twist_turn(world: World, twist: Twist, problem: Problem) -> None:
    world.say(twist.reveal)
    world.say(twist.turn.replace("{place}", problem.place))


def resolve(world: World, cat: Entity, farmer: Entity, solution: Solution,
            problem: Problem, twist: Twist) -> None:
    cat.meters["safe"] += 1
    cat.meters["helped"] += 1
    cat.memes["relief"] += 1
    farmer.memes["relief"] += 1
    world.say(
        f"Together they used {solution.tool}, and soon the barn was humming again."
    )
    world.say(
        f"{solution.effect} {solution.followup} By supper time, Pussy was purring on the "
        f"windowsill, and the whole place smelled like a promise kept."
    )
    world.say(twist.lesson)


def tell(problem: Problem, solution: Solution, twist: Twist,
         cat_name: str = "Pussy", farmer_name: str = "Milo") -> World:
    world = World()
    cat = world.add(Entity(id=cat_name, kind="character", type="cat", role="cat", label="Pussy"))
    farmer = world.add(Entity(id=farmer_name, kind="character", type="farmer", role="farmer", label="the farmer"))
    world.add(Entity(id="barn", type="place", label=problem.place))
    world.facts["helped"] = True

    open_scene(world, cat, farmer, problem)
    world.para()
    describe_need(world, cat, problem)
    pred = predict(world, problem)
    if pred["stuck"]:
        attempt(world, cat, solution, problem)
        world.para()
        twist_turn(world, twist, problem)
        cat.meters["stuck"] += 1
        cat.meters["fullness"] += 1
        propagate(world, narrate=False)
        world.say(
            f"The twist was this: the missing {problem.needs} was not missing at all. "
            f"It had been tucked inside a hollow Swiss cheese wheel the whole time."
        )
        world.say(
            f"Pussy laughed, the farmer laughed, and the two of them solved the "
            f"{problem.label} in the cheesiest way a barn ever saw."
        )
        world.para()
        resolve(world, cat, farmer, solution, problem, twist)
    world.facts.update(problem=problem, solution=solution, twist=twist, cat=cat, farmer=farmer)
    return world


@dataclass
class StoryParams:
    problem: str
    solution: str
    twist: str
    cat_name: str = "Pussy"
    farmer_name: str = "Milo"
    seed: Optional[int] = None


PROBLEMS = {
    "feed": Problem(id="feed", label="feed", place="feed room", needs="corn", risk="hungry hens", tags={"barn", "feed"}),
    "gate": Problem(id="gate", label="gate", place="north gate", needs="rope", risk="wandering goats", tags={"barn", "gate"}),
    "trough": Problem(id="trough", label="trough", place="water trough", needs="water", risk="thirsty horses", tags={"barn", "water"}),
}

SOLUTIONS = {
    "ladder": Solution(id="ladder", label="ladder", tool="a ladder and a steady paw", method="shimmied up and peered inside", effect="The ladder reached the rafters,", followup="and there, like a silver wink, sat the answer.", power=2, tags={"tool"}),
    "knot": Solution(id="knot", label="knot", tool="a length of rope", method="tied a clever knot", effect="The knot held fast,", followup="and the gate stopped wobbling.", power=2, tags={"tool"}),
    "bucket": Solution(id="bucket", label="bucket", tool="a bucket and a brave trot", method="trotted to the pump", effect="The bucket came back full,", followup="and the trough sang with water again.", power=2, tags={"tool"}),
}

TWISTS = {
    "swiss": Twist(id="swiss", reveal="Then came the twist: the barn had a lump of Swiss cheese on the workbench, yellow as sunrise.", turn="The cheese had a round hole in it, and that hole fit the missing {place} clue exactly.", lesson="Pussy learned that a funny-looking thing can be the very thing that solves the problem.", tags={"swiss", "twist"}),
    "shadow": Twist(id="shadow", reveal="Then came the twist: the shadow on the floor was not from a bat at all.", turn="It was from a little pulley that had slipped behind the {place}.", lesson="Pussy learned to look twice before calling a thing a mystery.", tags={"twist"}),
    "swap": Twist(id="swap", reveal="Then came the twist: the missing part had been borrowed, not lost.", turn="A neighbor had swapped it by mistake and left a note on the {place}.", lesson="Pussy learned that asking neighbors can solve a problem faster than fretting.", tags={"twist"}),
}

GIRL_NAMES = ["Pussy", "Mina", "Lulu"]
BOY_NAMES = ["Milo", "Jeb", "Otis"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale barn storyworld with a cat, Swiss cheese, and a twist.")
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--twist", choices=TWISTS)
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
    if args.problem and args.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    if args.solution and args.solution not in SOLUTIONS:
        raise StoryError("Unknown solution.")
    if args.twist and args.twist not in TWISTS:
        raise StoryError("Unknown twist.")
    p = args.problem or rng.choice(sorted(PROBLEMS))
    s = args.solution or rng.choice(sorted(SOLUTIONS))
    t = args.twist or rng.choice(sorted(TWISTS))
    if p not in PROBLEMS or s not in SOLUTIONS or t not in TWISTS:
        raise StoryError("(No valid combination matches the given options.)")
    return StoryParams(problem=p, solution=s, twist=t)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale barn story that includes the words "pussy" and "swiss".',
        f"Tell a funny problem-solving story about {f['cat'].id}, a barn trouble, and a twist with Swiss cheese.",
        f"Write a child-friendly tale where a clever cat solves a problem, learns a lesson, and the ending turns on a surprise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: Problem = world.facts["problem"]
    s: Solution = world.facts["solution"]
    t: Twist = world.facts["twist"]
    return [
        QAItem(question="Who is the story about?",
               answer=f"It is about Pussy, the barn cat, and the farmer who works beside her. Together they face a problem and find a fix."),
        QAItem(question=f"What problem did they solve?",
               answer=f"They solved the {p.label} problem in the {p.place}. It needed {p.needs}, and Pussy helped find a way to get it."),
        QAItem(question="What was the twist?",
               answer=f"The twist was that the answer was hidden inside a Swiss cheese wheel. What looked like a snack turned out to be the clue they needed."),
        QAItem(question="What lesson did Pussy learn?",
               answer=f"Pussy learned that a strange-looking thing can still be useful, and that looking closely can solve a problem faster than worrying."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is Swiss cheese?",
               answer="Swiss cheese is a kind of cheese with holes in it. People often notice it because of those holes."),
        QAItem(question="What does a barn do?",
               answer="A barn is a building where farm animals, tools, and feed are often kept. It helps keep farm work organized."),
        QAItem(question="What does a cat do when it is happy?",
               answer="A happy cat may purr, blink slowly, and curl up in a warm spot. Cats often show comfort in quiet little ways."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"- {p}" for p in sample.prompts], "", "== story qa =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.problem not in PROBLEMS or params.solution not in SOLUTIONS or params.twist not in TWISTS:
        raise StoryError("Invalid params.")
    world = tell(PROBLEMS[params.problem], SOLUTIONS[params.solution], TWISTS[params.twist],
                 cat_name=params.cat_name, farmer_name=params.farmer_name)
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
        print("--- world model state ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, e.meters, e.memes, e.role)
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
valid(P,S,T) :- problem(P), solution(S), twist(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
    for s in SOLUTIONS:
        lines.append(asp.fact("solution", s))
    for t in TWISTS:
        lines.append(asp.fact("twist", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py != cl:
        print("MISMATCH in valid_combos")
        rc = 1
    else:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    try:
        sample = generate(StoryParams(problem="feed", solution="ladder", twist="swiss"))
        if not sample.story:
            raise RuntimeError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


CURATED = [
    StoryParams(problem="feed", solution="ladder", twist="swiss", cat_name="Pussy", farmer_name="Milo"),
    StoryParams(problem="gate", solution="knot", twist="shadow", cat_name="Pussy", farmer_name="Reed"),
    StoryParams(problem="trough", solution="bucket", twist="swap", cat_name="Pussy", farmer_name="June"),
]


def explain_rejection(_: Any) -> str:
    return "(No story: that combination does not make a good barn tale.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for p, s, t in combos:
            print(p, s, t)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
