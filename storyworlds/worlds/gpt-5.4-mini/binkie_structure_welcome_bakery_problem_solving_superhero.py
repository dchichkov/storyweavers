#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/binkie_structure_welcome_bakery_problem_solving_superhero.py
=============================================================================================

A standalone storyworld for a tiny superhero-style bakery problem-solving tale.

Seed premise:
- setting: bakery
- style: superhero story
- features: problem solving
- seed words: binkie, structure, welcome

The simulated domain: a child hero visits a bakery with a binkie, notices a
fallen pastry display structure, and uses a calm problem-solving plan to make the
bakery safe and welcoming again.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Bakery:
    id: str
    name: str
    welcome_phrase: str
    smells: str
    hero_title: str
    helper_title: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    effect: str
    danger: str
    fix_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    bakery: Bakery
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.bakery)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_problem_spreads(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["problem"] < THRESHOLD:
            continue
        sig = ("problem_spreads", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("bakery").meters["uneasy"] += 1
        for kid in world.entities.values():
            if kid.role in {"hero", "helper"}:
                kid.memes["concern"] += 1
        out.append("__problem__")
    return out


CAUSAL_RULES = [Rule("problem_spreads", _r_problem_spreads)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
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
    return produced


def bakery_problem(bakery: Bakery, problem: Problem) -> bool:
    return bakery.id == "bakery" and problem.id in {"fallen_structure", "crowded_counter"}


def best_fix() -> "Fix":
    return max(FIXES.values(), key=lambda f: f.skill)


@dataclass
class Fix:
    id: str
    skill: int
    power: int
    text: str
    fail: str
    tags: set[str] = field(default_factory=set)


def is_solved(fix: Fix, problem: Problem) -> bool:
    return fix.power >= 1


def _do_problem(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["problem"] += 1
    propagate(world, narrate=narrate)


def open_scene(world: World, hero: Entity, helper: Entity, bakery: Bakery, problem: Problem) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"On a bright morning, {hero.id} and {helper.id} stepped into {bakery.name}. "
        f"{bakery.smells} and the shelves shone like a friendly city."
    )
    world.say(
        f'{bakery.welcome_phrase} said the baker, and {hero.id} smiled under '
        f"{hero.pronoun('possessive')} cape."
    )
    world.say(
        f"{hero.id} was ready to be a small superhero, but then {problem.label} "
        f"made the bakery wobble."
    )


def discover(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    hero.memes["alert"] += 1
    helper.memes["alert"] += 1
    world.say(
        f"Near the display, {helper.id} pointed and gasped. {problem.effect} "
        f"{problem.danger}"
    )
    world.say(
        f'"We can fix this," {hero.id} said. "A hero helps, not hides."'
    )


def plan(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    hero.memes["thinking"] += 1
    helper.memes["thinking"] += 1
    world.say(
        f"{helper.id} noticed {problem.fix_hint}, and the two friends made a plan."
    )
    world.say(
        f"They would clear the floor, steady the structure, and keep the welcome "
        f"happy for every customer."
    )


def act_fix(world: World, hero: Entity, helper: Entity, fix: Fix, problem_ent: Entity) -> None:
    problem_ent.meters["problem"] = 0.0
    world.get("bakery").meters["uneasy"] = 0.0
    hero.memes["pride"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"{hero.id} used {fix.text}. {helper.id} held the tray steady while {hero.id} "
        f"made the broken structure strong again."
    )
    world.say(
        f"The problem faded, and the bakery felt calm."
    )


def welcome_end(world: World, hero: Entity, helper: Entity, bakery: Bakery) -> None:
    hero.memes["love"] += 1
    helper.memes["love"] += 1
    world.say(
        f"At the end, {bakery.welcome_phrase.lower()} seemed even warmer than before."
    )
    world.say(
        f"People came in, saw the neat shelves, and smiled. {hero.id} stood tall in "
        f"{hero.pronoun('possessive')} cape, proud that the bakery was safe and welcoming again."
    )


def tell(bakery: Bakery, problem: Problem, fix: Fix,
         hero_name: str = "Milo", hero_gender: str = "boy",
         helper_name: str = "Nina", helper_gender: str = "girl") -> World:
    world = World(bakery)
    hero = world.add(Entity(hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(helper_name, kind="character", type=helper_gender, role="helper"))
    baker = world.add(Entity("Baker", kind="character", type="adult", role="adult", label="the baker"))
    structure = world.add(Entity("structure", type="structure", label="the pastry structure"))
    binkie = world.add(Entity("binkie", type="thing", label="the binkie"))
    world.facts["binkie"] = binkie.id
    world.facts["structure"] = structure.id
    world.facts["welcome"] = bakery.welcome_phrase

    open_scene(world, hero, helper, bakery, problem)
    world.para()
    discover(world, hero, helper, problem)
    plan(world, hero, helper, problem)
    _do_problem(world, structure)
    world.para()
    act_fix(world, hero, helper, fix, structure)
    welcome_end(world, hero, helper, bakery)

    world.facts.update(
        hero=hero, helper=helper, baker=baker, problem=problem, fix=fix,
        resolved=True, structure=structure, binkie=binkie,
    )
    return world


BAKERIES = {
    "bakery": Bakery(
        "bakery", "Sunrise Bakery",
        "Welcome to Sunrise Bakery!",
        "Sweet bread smells filled the room.",
        "hero", "helper",
        tags={"bakery", "welcome"},
    )
}

PROBLEMS = {
    "fallen_structure": Problem(
        "fallen_structure",
        "a pastry structure leaning sideways",
        "The cookie tower had tipped over.",
        "It blocked the path and made the front display look messy.",
        "The hero could steady it and reset the trays.",
        tags={"structure", "problem"},
    ),
    "crowded_counter": Problem(
        "crowded_counter",
        "a crowded counter",
        "The counter was getting piled too high.",
        "It was hard for customers to see where to stand.",
        "The hero could clear space and make a new line.",
        tags={"welcome", "problem"},
    ),
}

FIXES = {
    "steady": Fix(
        "steady", 3, 1,
        "carefully braced the shelves and straightened the tray stand",
        "tried to steady the shelves, but the wobble was too much",
        tags={"structure"},
    ),
    "clear": Fix(
        "clear", 2, 1,
        "moved the extra boxes out of the way and cleared the path",
        "moved the boxes, but the path was still blocked",
        tags={"welcome"},
    ),
    "tie": Fix(
        "tie", 2, 1,
        "used a ribbon to tie the sign and keep it from slipping",
        "tied the sign, but it still tilted",
        tags={"structure"},
    ),
}

GIRL_NAMES = ["Nina", "Maya", "Lina", "Ruby", "Ivy"]
BOY_NAMES = ["Milo", "Theo", "Owen", "Eli", "Noah"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for bid, bakery in BAKERIES.items():
        for pid, problem in PROBLEMS.items():
            if bakery_problem(bakery, problem):
                for fid, fix in FIXES.items():
                    if is_solved(fix, problem):
                        out.append((bid, pid, fid))
    return out


@dataclass
class StoryParams:
    bakery: str
    problem: str
    fix: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, problem = f["hero"], f["helper"], f["problem"]
    return [
        'Write a superhero story set in a bakery that includes the words "binkie", "structure", and "welcome".',
        f"Tell a short story where {hero.id} and {helper.id} solve {problem.label} in a bakery and keep the welcome warm.",
        f"Write a child-friendly problem-solving story about a bakery hero who notices a structure problem and helps fix it.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper, problem, fix = f["hero"], f["helper"], f["problem"], f["fix"]
    return [
        ("Where does the story happen?",
         f"It happens in the bakery, where sweet bread smells filled the room and the welcome sign greeted everyone."),
        ("What problem did they notice?",
         f"They noticed {problem.label}. The broken structure made the front of the bakery look messy and a little unsafe."),
        ("How did they solve it?",
         f"{hero.id} and {helper.id} used teamwork. {hero.id} {fix.text}, and together they made the bakery calm again."),
        ("Why was the ending happy?",
         f"The structure was fixed and the bakery felt welcoming again. Customers could come in and smile at the neat display."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a bakery?",
         "A bakery is a place where bread, cakes, and pastries are made and sold."),
        ("What is a binkie?",
         "A binkie is a baby pacifier. It helps some babies feel calm and comfortable."),
        ("What does welcome mean?",
         "Welcome means friendly and glad to see someone arrive."),
        ("What does structure mean?",
         "A structure is something built with parts that hold it together, like a shelf or tower."),
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
    lines.append("== (3) World-knowledge questions ==")
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(problem: Problem) -> str:
    return f"(No story: the bakery problem '{problem.label}' does not fit this tiny problem-solving world.)"


ASP_RULES = r"""
valid(B,P,F) :- bakery(B), problem(P), fix(F), supports(F,P), bakery_problem(B,P).
"""  # a compact twin for the Python validity gate


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for bid in BAKERIES:
        lines.append(asp.fact("bakery", bid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("bakery_problem", "bakery", pid))
    for fid, fx in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("supports", fid, "fallen_structure" if "structure" in fx.tags else "crowded_counter"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP and Python validity differ.")
    try:
        sample = generate(resolve_params(argparse.Namespace(bakery=None, problem=None, fix=None, hero=None, hero_gender=None, helper=None, helper_gender=None), random.Random(1)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero bakery problem-solving storyworld.")
    ap.add_argument("--bakery", choices=BAKERIES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    if args.problem and args.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    if args.problem and args.fix and (args.bakery or "bakery") == "bakery":
        if not is_solved(FIXES[args.fix], PROBLEMS[args.problem]):
            raise StoryError(explain_rejection(PROBLEMS[args.problem]))
    filtered = [c for c in combos
                if (args.bakery is None or c[0] == args.bakery)
                and (args.problem is None or c[1] == args.problem)
                and (args.fix is None or c[2] == args.fix)]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    bakery, problem, fix = rng.choice(filtered)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero])
    return StoryParams(bakery, problem, fix, hero, hero_gender, helper, helper_gender)


CURATED = [
    StoryParams("bakery", "fallen_structure", "steady", "Milo", "boy", "Nina", "girl"),
    StoryParams("bakery", "crowded_counter", "clear", "Maya", "girl", "Theo", "boy"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(BAKERIES[params.bakery], PROBLEMS[params.problem], FIXES[params.fix],
                 params.hero, params.hero_gender, params.helper, params.helper_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(f"{len(asp_valid_combos())} compatible combos:")
        for b, p, f in asp_valid_combos():
            print(f"  {b} {p} {f}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
