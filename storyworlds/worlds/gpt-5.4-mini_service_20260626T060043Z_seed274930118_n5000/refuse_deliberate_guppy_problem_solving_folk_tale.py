#!/usr/bin/env python3
"""
storyworlds/worlds/refuse_deliberate_guppy_problem_solving_folk_tale.py
=======================================================================

A small folk-tale story world about a guppy in trouble, a careful refusal,
and a deliberate problem-solving choice that helps everyone.

Seed-tale idea:
A child finds a tiny guppy in a shallow bowl after the stream dries. The child
first refuses to waste time guessing, then deliberately thinks through the
problem with a grandparent. They choose a safe carrying vessel, move the guppy
with care, and return it to water before the little fish grows weaker.

The world models:
- physical meters: water level, dryness, safety, distance
- emotional memes: worry, patience, resolve, relief, trust

The prose is intentionally folk-tale-like: simple, concrete, and causal.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    contains: Optional[str] = None
    portable: bool = False
    safe_water: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["water", "dryness", "distance", "safety"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "patience", "resolve", "relief", "trust"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    water: float
    dry: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Container:
    id: str
    label: str
    phrase: str
    holds_water: bool
    shallow: bool
    portable: bool


@dataclass
class StoryParams:
    place: str
    problem: str
    solution: str
    name: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_dryness(world: World) -> list[str]:
    out = []
    guppy = world.get("guppy")
    bowl = world.get("bowl")
    if bowl.contains == "guppy" and not bowl.safe_water:
        sig = ("dry",)
        if sig not in world.fired:
            world.fired.add(sig)
            guppy.meters["dryness"] += 1
            guppy.memes["worry"] += 1
            out.append("The guppy grew drier and more worried.")
    return out


def _r_relief(world: World) -> list[str]:
    out = []
    guppy = world.get("guppy")
    pond = world.place
    if guppy.meters["water"] >= THRESHOLD and guppy.meters["safety"] >= THRESHOLD:
        sig = ("relief",)
        if sig not in world.fired:
            world.fired.add(sig)
            guppy.memes["relief"] += 1
            guppy.memes["trust"] += 1
            out.append(f"The little fish settled as if it knew the pond was waiting.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_dryness, _r_relief):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_world(place: Place, problem: str, solution: str, name: str, helper: str) -> World:
    world = World(place)
    child = world.add(Entity(id="child", kind="character", type="child", label=name))
    elder = world.add(Entity(id="elder", kind="character", type="elder", label=helper))
    guppy = world.add(Entity(id="guppy", kind="creature", type="guppy", label="tiny guppy"))
    bowl = world.add(Entity(id="bowl", type="bowl", label="clay bowl", phrase="a clay bowl", caretaker="child"))
    bowl.contains = "guppy"
    bowl.safe_water = False
    guppy.meters["water"] = 0.5
    guppy.meters["safety"] = 0.2

    world.say(f"{name} found a tiny guppy in a clay bowl by {place.label}.")
    world.say(f"The child did not rush. Instead, {name} would not refuse the problem itself; {name} refused to guess.")
    world.say(f"With {helper}, {name} chose to deliberate, because a small life deserved a careful answer.")

    world.para()
    if problem == "dry_stream":
        world.say(f"The stream was dry, and the guppy needed water soon.")
    elif problem == "deep_container":
        world.say(f"The bowl was too deep and slippery for the guppy to climb out alone.")
    else:
        world.say(f"The path back to water was long enough to tire a tiny fish.")

    world.say(f"{name} and {helper} looked at the bowl, the stream, and the path between them.")
    world.say(f"They refused to hurry past the choice and instead worked it through step by step.")

    world.para()
    if solution == "leaf_boat":
        world.say(f"{helper} found a broad leaf and folded it like a little boat.")
        world.say(f"{name} gently tipped the guppy onto the leaf with a spoonful of water.")
    elif solution == "shallow_bucket":
        world.say(f"{helper} fetched a shallow bucket with cool water in the bottom.")
        world.say(f"{name} moved the guppy into it one careful spoon at a time.")
    else:
        world.say(f"{helper} brought a wet cloth and a tin cup, and together they made a safer path.")
        world.say(f"{name} used the cup to carry the guppy without shaking it.")

    guppy.meters["water"] += 1.0
    guppy.meters["safety"] += 1.0
    propagate(world, narrate=True)

    world.say(f"At last, they carried the guppy back to the water by {place.label}.")
    world.say(f"The guppy swam free, and {name} smiled at the wise, deliberate way the problem had been solved.")

    world.facts.update(
        child=child,
        elder=elder,
        guppy=guppy,
        bowl=bowl,
        place=place,
        problem=problem,
        solution=solution,
    )
    return world


PLACES = {
    "spring": Place(id="spring", label="the spring", water=1.0, affords={"leaf_boat", "shallow_bucket", "wet_cup"}),
    "riverbank": Place(id="riverbank", label="the riverbank", water=1.0, affords={"leaf_boat", "shallow_bucket", "wet_cup"}),
    "pond": Place(id="pond", label="the pond", water=1.0, affords={"leaf_boat", "shallow_bucket", "wet_cup"}),
}

PROBLEMS = {
    "dry_stream": "dry_stream",
    "deep_container": "deep_container",
    "long_path": "long_path",
}

SOLUTIONS = {
    "leaf_boat": Container(id="leaf_boat", label="leaf boat", phrase="a broad leaf folded like a boat", holds_water=False, shallow=True, portable=True),
    "shallow_bucket": Container(id="shallow_bucket", label="shallow bucket", phrase="a shallow bucket with cool water", holds_water=True, shallow=True, portable=True),
    "wet_cup": Container(id="wet_cup", label="wet cup", phrase="a tin cup kept wet and steady", holds_water=True, shallow=True, portable=True),
}

NAMES = ["Mina", "Ivo", "Sana", "Tavi", "Lio", "Nera", "Pavel", "Mara"]
HELPERS = ["grandmother", "grandfather", "aunt", "uncle", "old fisher"]
TRAITS = ["patient", "kind", "careful", "steady", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for prob in PROBLEMS:
            for sol in SOLUTIONS:
                if sol in place.affords:
                    combos.append((pid, prob, sol))
    return combos


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for s in sorted(place.affords):
            lines.append(asp.fact("affords", pid, s))
    for prob in PROBLEMS:
        lines.append(asp.fact("problem", prob))
    for sol, c in SOLUTIONS.items():
        lines.append(asp.fact("solution", sol))
        if c.holds_water:
            lines.append(asp.fact("holds_water", sol))
        if c.shallow:
            lines.append(asp.fact("shallow", sol))
        if c.portable:
            lines.append(asp.fact("portable", sol))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(P, Prob, Sol) :- place(P), problem(Prob), solution(Sol), affords(P, Sol).
#show compatible/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
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
    ap = argparse.ArgumentParser(description="A folk-tale story world about a guppy, careful refusal, and problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.solution is None or c[2] == args.solution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, solution = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, problem=problem, solution=solution, name=name, helper=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short folk tale for a young child about a guppy, a refusal to rush, and a deliberate solution.',
        f"Tell a gentle story where {f['child'].label} and {f['elder'].label} solve a problem for a tiny guppy by thinking carefully.",
        f'Write a simple story that includes the words "refuse", "deliberate", and "guppy" and ends with the fish safely back in water.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    elder: Entity = f["elder"]
    guppy: Entity = f["guppy"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"Who found the guppy near {place.label}?",
            answer=f"{child.label} found the tiny guppy near {place.label}, and {elder.label} helped think through the problem.",
        ),
        QAItem(
            question=f"What did {child.label} refuse to do at first?",
            answer=f"{child.label} refused to guess or rush. Instead, {child.label} and {elder.label} deliberately looked for a safer way to help the guppy.",
        ),
        QAItem(
            question="How was the problem solved?",
            answer=f"They chose a careful tool, moved the guppy with water and steadiness, and returned it to the water by {place.label}.",
        ),
        QAItem(
            question="What changed for the guppy by the end?",
            answer=f"The guppy was no longer stuck in the bowl. It had more water, more safety, and swam free again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a guppy?",
            answer="A guppy is a tiny freshwater fish. It needs water around it to stay alive and safe.",
        ),
        QAItem(
            question="What does deliberate mean?",
            answer="Deliberate means slow and careful on purpose, like thinking before acting.",
        ),
        QAItem(
            question="What does refuse mean?",
            answer="Refuse means to say no or not agree to do something.",
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
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.contains:
            bits.append(f"contains={e.contains}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(PLACES[params.place], params.problem, params.solution, params.name, params.helper)
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
    StoryParams(place="pond", problem="dry_stream", solution="leaf_boat", name="Mina", helper="grandmother"),
    StoryParams(place="riverbank", problem="long_path", solution="shallow_bucket", name="Tavi", helper="old fisher"),
    StoryParams(place="spring", problem="deep_container", solution="wet_cup", name="Sana", helper="aunt"),
]


def asp_verify_story(params: StoryParams) -> None:
    sample = generate(params)
    if not sample.story or "guppy" not in sample.story.lower():
        raise StoryError("verification failed: story missing guppy")
    if "refuse" not in sample.story.lower() and "deliberate" not in sample.story.lower():
        raise StoryError("verification failed: story missing core seed words")


def asp_verify_all() -> int:
    if set(asp_valid_combos()) != set(valid_combos()):
        return asp_verify()
    for p in CURATED:
        asp_verify_story(p)
    print(f"OK: clingo gate matches valid_combos() and {len(CURATED)} sample stories verify.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify_all())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, problem, solution) combos:\n")
        for place, prob, sol in combos:
            print(f"  {place:10} {prob:15} {sol}")
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
            header = f"### {p.name}: {p.problem} at {p.place} (solution: {p.solution})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
