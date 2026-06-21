#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tour_woof_spurt_problem_solving_humor_animal.py
===============================================================================

A tiny animal-story world about a tour, a surprise woof, and a spurt of water.

Premise
-------
A small animal group goes on a little tour, runs into a funny problem, and
solves it together with a clever, child-friendly fix.

This world is built to support:
- Problem Solving
- Humor
- Animal Story style

It keeps the story compact and state-driven:
- a tour route,
- a noisy or messy snag,
- a playful animal response,
- a practical repair,
- and a closing image that proves the problem changed.

The story always includes the words:
- tour
- woof
- spurt

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/tour_woof_spurt_problem_solving_humor_animal.py
    python storyworlds/worlds/gpt-5.4-mini/tour_woof_spurt_problem_solving_humor_animal.py --all
    python storyworlds/worlds/gpt-5.4-mini/tour_woof_spurt_problem_solving_humor_animal.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/tour_woof_spurt_problem_solving_humor_animal.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2

ANIMAL_FORMS = {
    "fox": {"type": "fox", "sound": "woof", "plural": False, "pronouns": ("it", "it", "its")},
    "dog": {"type": "dog", "sound": "woof", "plural": False, "pronouns": ("he", "him", "his")},
    "goat": {"type": "goat", "sound": "woof", "plural": False, "pronouns": ("she", "her", "her")},
    "raccoon": {"type": "raccoon", "sound": "woof", "plural": False, "pronouns": ("they", "them", "their")},
}

TOURS = {
    "bakery": {
        "place": "the bakery tour",
        "route": "past the warm ovens and the shiny bread shelves",
        "goal": "see the fancy bread",
        "ending": "they waved at the baker and left with flour on their paws and smiles on their faces",
    },
    "garden": {
        "place": "the garden tour",
        "route": "past the bean trellis and the buzzing flowers",
        "goal": "visit the tomato patch",
        "ending": "they skipped home with a sprig of mint and a lot to laugh about",
    },
    "pond": {
        "place": "the pond tour",
        "route": "past the reeds and the wobbling duck dock",
        "goal": "watch the tadpoles",
        "ending": "they trotted off with damp paws and a new story to tell",
    },
}

PROBLEMS = {
    "mud": {
        "label": "mud puddle",
        "risk": "it made the path too slippery",
        "mess": "muddy",
        "humor": "the mud made a silly splat sound",
    },
    "gate": {
        "label": "wobbly gate",
        "risk": "it blocked the way with a squeak and a clank",
        "mess": "stuck",
        "humor": "the gate kept making a grumpy groan",
    },
    "basket": {
        "label": "snack basket",
        "risk": "it tipped and rolled away",
        "mess": "spilled",
        "humor": "the crackers bounced like tiny moons",
    },
}

FIXES = {
    "plank": {
        "label": "a plank",
        "action": "laid a plank across it",
        "effect": "made a safe bridge",
        "power": 2,
        "sense": 3,
    },
    "rope": {
        "label": "a rope",
        "action": "looped a rope around it and tugged it straight",
        "effect": "held the path in place",
        "power": 2,
        "sense": 3,
    },
    "bucket": {
        "label": "a bucket",
        "action": "carried a bucket over and gave the problem a careful splash",
        "effect": "washed the mess aside",
        "power": 3,
        "sense": 3,
    },
    "leaf": {
        "label": "a leaf",
        "action": "used a leaf like a fix",
        "effect": "did almost nothing",
        "power": 0,
        "sense": 1,
    },
}

GADGETS = {
    "spray": {"label": "spray bottle", "kind": "tool", "meters": {"water": 1.0}},
    "cloth": {"label": "clean cloth", "kind": "tool", "meters": {"soft": 1.0}},
    "whistle": {"label": "toy whistle", "kind": "toy", "meters": {"noise": 1.0}},
}

GIRL_NAMES = ["Mina", "Luna", "Pip", "Nora", "Zara"]
BOY_NAMES = ["Toby", "Finn", "Ollie", "Bram", "Milo"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    sound: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"dog", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"goat", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    tour: str
    problem: str
    fix: str
    animal: str
    name: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="An animal tour story with a woof, a spurt, and a fix.")
    ap.add_argument("--tour", choices=TOURS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--animal", choices=ANIMAL_FORMS)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["friend", "guide"])
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for t in TOURS:
        for p in PROBLEMS:
            for f in FIXES:
                if FIXES[f]["sense"] >= SENSE_MIN and FIXES[f]["power"] >= 2:
                    combos.append((t, p, f))
    return combos


def explain_rejection(fix: str) -> str:
    return f"(No story: fix '{fix}' is too weak or too silly for a solid problem-solving ending.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and FIXES[args.fix]["sense"] < SENSE_MIN:
        raise StoryError(explain_rejection(args.fix))
    combos = [c for c in valid_combos()
              if (args.tour is None or c[0] == args.tour)
              and (args.problem is None or c[1] == args.problem)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    tour, problem, fix = rng.choice(sorted(combos))
    animal = args.animal or rng.choice(sorted(ANIMAL_FORMS))
    form = ANIMAL_FORMS[animal]
    name = args.name or rng.choice(GIRL_NAMES if form["type"] in {"goat"} else BOY_NAMES)
    helper = args.helper or rng.choice(["friend", "guide"])
    return StoryParams(tour=tour, problem=problem, fix=fix, animal=animal, name=name, helper=helper)


def tell(params: StoryParams) -> World:
    w = World()
    animal = w.add(Entity(id=params.name, kind="character", type=ANIMAL_FORMS[params.animal]["type"],
                          sound=ANIMAL_FORMS[params.animal]["sound"], role="hero"))
    helper = w.add(Entity(id="Helper", kind="character", type="raccoon", label=params.helper, role="helper"))
    problem = w.add(Entity(id="problem", type="thing", label=PROBLEMS[params.problem]["label"], tags={params.problem}))
    gadget = w.add(Entity(id="gadget", type="tool", label=GADGETS["spray"]["label"], tags={"tool"}))
    animal.memes["curiosity"] += 1
    animal.memes["humor"] += 1
    w.say(
        f"{animal.id} joined a small tour through {TOURS[params.tour]['route']}. "
        f"{animal.id} wanted to {TOURS[params.tour]['goal']}."
    )
    w.say(
        f"Then {problem.label} caused trouble because {PROBLEMS[params.problem]['risk']}. "
        f"{PROBLEMS[params.problem]['humor']}"
    )
    w.para()
    w.say(f"{animal.id} gave a cheerful {animal.sound}: \"woof!\"")
    w.say(f"{helper.label.capitalize()} said, \"Let's think of a fix.\"")
    fix = FIXES[params.fix]
    if fix["sense"] >= SENSE_MIN:
        animal.memes["problem_solving"] += 1
        problem.meters["trouble"] += 1
        if fix["power"] >= 2:
            problem.meters["resolved"] += 1
            problem.meters["spurt"] += 1
            w.say(
                f"{animal.id} {fix['action']}. With a little spurt of water, the path {fix['effect']}."
            )
            w.say(
                f"The tour could go on, and soon {animal.id} was happily looking at {TOURS[params.tour]['ending']}."
            )
        else:
            w.say(f"{animal.id} tried to help, but the problem stayed put.")
    w.facts.update(params=params, animal=animal, helper=helper, problem=problem, fix=fix)
    return w


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write an animal story that includes the words tour, woof, and spurt.",
        f"Tell a funny story about {p.name} the {p.animal} on a tour who solves a small problem with a clever fix.",
        f"Write a short problem-solving animal story with a harmless mishap and a cheerful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(question="Who is the story about?", answer=f"It is about {p.name}, a little {p.animal}, who joins a tour and helps solve a problem. The animal's funny woof and the spurt are both part of the trouble and the fix."),
        QAItem(question="What problem came up on the tour?", answer=f"A {PROBLEMS[p.problem]['label']} caused trouble and made the route harder to cross. The animals had to slow down and think before they could keep going."),
        QAItem(question="How was the problem solved?", answer=f"{p.name} used {FIXES[p.fix]['label']} and turned the mess into something manageable. That clever choice let the tour continue instead of stopping in a fuss."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a tour?", answer="A tour is a little trip where you visit places and look around together. It can be fun because you see new things and learn as you go."),
        QAItem(question="What does woof mean?", answer="Woof is the sound a dog makes. People use it in stories when an animal is being playful or noisy."),
        QAItem(question="What is a spurt?", answer="A spurt is a quick burst or splash of liquid. It comes out fast and then stops."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("\n== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.type:7}) meters={dict(e.meters)} memes={dict(e.memes)} attrs={e.attrs} tags={sorted(e.tags)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(tour="bakery", problem="mud", fix="plank", animal="dog", name="Milo", helper="guide"),
    StoryParams(tour="garden", problem="gate", fix="rope", animal="fox", name="Pip", helper="friend"),
    StoryParams(tour="pond", problem="basket", fix="bucket", animal="goat", name="Nora", helper="guide"),
]


def generate(params: StoryParams) -> StorySample:
    if params.tour not in TOURS or params.problem not in PROBLEMS or params.fix not in FIXES or params.animal not in ANIMAL_FORMS:
        raise StoryError("invalid story parameters")
    world = tell(params)
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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
valid(T,P,F) :- tour(T), problem(P), fix(F), good_fix(F).
"""
def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for t in TOURS:
        lines.append(asp.fact("tour", t))
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
    for f, cfg in FIXES.items():
        lines.append(asp.fact("fix", f))
        if cfg["sense"] >= SENSE_MIN:
            lines.append(asp.fact("good_fix", f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python combo gates differ.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        return 1 if (print(f"SMOKE TEST FAILED: {exc}") is None) else 1
    if rc == 0:
        print("OK: ASP and Python combo gates match.")
    return rc


def build_sample_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for t, p, f in combos:
            print(f"{t:10} {p:10} {f}")
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
                params = build_sample_from_args(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
