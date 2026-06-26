#!/usr/bin/env python3
"""
storyworlds/worlds/tubing_incessant_whap_problem_solving_inner_monologue.py
===========================================================================

A small folk-tale storyworld about a noisy tubing problem, a steady mind, and
a clever fix.

Seed tale:
---
Long ago, in a little village by a hill, a young helper was sent to carry water
through a narrow tube. But the tube kept making an incessant whap-whap-whap
against the cart, and the water would not flow right. The helper grew worried,
listened to the sound, thought hard, and at last wrapped the tube, tied it
securely, and guided it into a better path. Then the water ran true, the whap
went quiet, and the helper smiled.

World idea:
- The physical problem is a tube that bangs, leaks, or kinks.
- The emotional turn is the hero's inner monologue: noticing, reasoning, trying,
  and then calming once the problem is solved.
- The ending proves the change with a quiet, working tube and a satisfied
  helper.

The world is intentionally small and constraint-checked: a noisy tubing problem
only becomes a story when there is a plausible repair.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    supports: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "mother", "queen", "maiden"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "king", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    noise: str
    mess: str
    danger: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    action: str
    result: str
    helps: set[str] = field(default_factory=set)


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _narrative_noise(problem: Problem) -> str:
    return {
        "whap": "whap-whap-whap",
        "rattle": "rattle-rattle",
        "sputter": "sputter-sputter",
    }.get(problem.noise, problem.noise)


def problem_at_risk(problem: Problem) -> bool:
    return True


def select_fix(problem: Problem) -> Optional[Fix]:
    for fx in FIXES:
        if problem.id in fx.helps:
            return fx
    return None


def reasonableness_gate(problem: Problem, fix: Optional[Fix]) -> bool:
    return problem_at_risk(problem) and fix is not None


def _resolve_fix(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.memes.get("trouble", 0.0) < THRESHOLD:
            continue
        if hero.memes.get("insight", 0.0) < THRESHOLD:
            continue
        if hero.meters.get("tension", 0.0) < THRESHOLD:
            continue
        if world.facts.get("fixed"):
            continue
        fx: Fix = world.facts["fix"]
        problem: Problem = world.facts["problem"]
        hero.meters["tension"] = 0.0
        hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1.0
        world.facts["fixed"] = True
        out.append(f"{hero.pronoun('subject').capitalize()} had found the way: {fx.result}.")
        out.append(f"The {problem.label} fell still at last.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        sents = _resolve_fix(world)
        if sents:
            changed = True
            produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, problem: Problem, fix: Fix, hero_name: str, hero_type: str, companion_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    companion = world.add(Entity(id=companion_name, kind="character", type="elder"))

    tubing = world.add(Entity(
        id="tubing",
        type="tube",
        label="tubing",
        phrase=problem.phrase,
        owner=hero.id,
        caretaker=companion.id,
    ))
    tool = world.add(Entity(
        id=fix.id,
        type="tool",
        label=fix.label,
        phrase=fix.phrase,
        protective=True,
        supports=set(fix.helps),
    ))

    world.facts.update(hero=hero, companion=companion, tubing=tubing, problem=problem, fix=fix, tool=tool)

    hero.memes["duty"] = 1.0
    hero.meters["tension"] = 0.0

    world.say(
        f"Long ago, {hero.id} was a small {hero_type} who had been given a task: "
        f"to carry water with {problem.phrase}."
    )
    world.say(
        f"But the tube would not behave. It kept making an incessant {_narrative_noise(problem)}, "
        f"and each {problem.noise} knocked against the cart like a small angry drum."
    )
    world.say(
        f"{hero.id} stood still and listened. In a quiet inner monologue, {hero.pronoun()} thought, "
        f"'{problem.danger}.'"
    )
    world.say(
        f"{hero.id} thought again, '{problem.mess}. But if I guide the tube better, maybe the water will run true.'"
    )

    hero.memes["trouble"] = 1.0
    hero.memes["insight"] = 1.0
    hero.meters["tension"] = 1.0

    world.para()
    world.say(
        f"So {hero.id} looked for a fix. {hero.pronoun('possessive').capitalize()} {companion.label} said, "
        f'"Use {fix.phrase}, and set the tube where it can rest."'
    )
    world.say(
        f"{hero.id} tried the plan: {fix.action}."
    )
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"Then the water flowed smoothly, the incessant {_narrative_noise(problem)} went quiet, "
        f"and {hero.id} smiled to hear the soft little trickle."
    )
    world.say(
        f"From that day on, the tubing stayed calm, and the village remembered how a careful thought can fix a noisy thing."
    )
    return world


SETTING = Setting(
    place="the village lane by the well",
    indoors=False,
    affords={"carry_water", "repair_tube"},
)

PROBLEMS = {
    "whap_tube": Problem(
        id="whap_tube",
        label="noisy tubing",
        phrase="a long length of tubing",
        noise="whap",
        mess="the water kept sloshing and the tube kept bumping the cart",
        danger="If I do nothing, the tube will kink and the water will spill",
        keyword="tubing",
        tags={"tubing", "whap", "incessant"},
    ),
    "rattle_tube": Problem(
        id="rattle_tube",
        label="shaking tubing",
        phrase="a bendy tube tied to the cart",
        noise="rattle",
        mess="the tube keeps knocking loose",
        danger="If I do nothing, the fittings will slip apart",
        keyword="tubing",
        tags={"tubing", "incessant"},
    ),
}

FIXES = [
    Fix(
        id="wrap",
        label="soft cloth wrap",
        phrase="a soft cloth wrap",
        action="wrap the tubing so it would not whip against the cart",
        result="the wrap cushioned the tube and stopped the whap",
        helps={"whap_tube"},
    ),
    Fix(
        id="tie",
        label="strong cord",
        phrase="a strong cord",
        action="tie the tubing fast to a smooth hook",
        result="the cord held the tubing steady and quiet",
        helps={"whap_tube", "rattle_tube"},
    ),
    Fix(
        id="reroute",
        label="wooden guide",
        phrase="a little wooden guide",
        action="guide the tubing along the side of the cart",
        result="the guide gave the tubing a better path",
        helps={"whap_tube", "rattle_tube"},
    ),
]

GIRL_NAMES = ["Mira", "Nella", "Oona", "Tilda", "Elin"]
BOY_NAMES = ["Perrin", "Rowan", "Cedric", "Bram", "Alfie"]
Elder_NAMES = ["Grandmother", "Old Piper", "Uncle Reed", "Aunt Willow"]

TRAITS = ["steady", "thoughtful", "brave", "patient", "clever"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in {"lane": SETTING}.items():
        for pid, prob in PROBLEMS.items():
            for fx in FIXES:
                if reasonableness_gate(prob, fx):
                    combos.append((place, pid, fx.id))
    return combos


@dataclass
class StoryParams:
    place: str
    problem: str
    fix: str
    name: str
    gender: str
    companion: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    problem: Problem = f["problem"]
    return [
        f'Write a folk-tale style story for a child about {hero.id} and the word "{problem.keyword}".',
        f"Tell a short story where {hero.id} faces an incessant {problem.noise} and solves the tubing problem with careful thought.",
        f"Write a simple tale with inner monologue, a noisy tube, and a clever repair that ends in quiet water.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    problem: Problem = f["problem"]
    fix: Fix = f["fix"]
    return [
        QAItem(
            question=f"What problem did {hero.id} have at the village lane?",
            answer=f"{hero.id} had to deal with {problem.phrase}, which kept making an incessant {problem.noise}.",
        ),
        QAItem(
            question=f"How did {hero.id} think about the trouble before acting?",
            answer=f"{hero.id} stopped, listened, and used an inner monologue to think through the problem instead of rushing.",
        ),
        QAItem(
            question=f"What did {companion.id} suggest to help?",
            answer=f"{companion.id} suggested {fix.phrase} and a steadier way to hold the tubing.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The tubing was fixed, the incessant {problem.noise} went quiet, and the water flowed smoothly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is tubing?",
            answer="Tubing is a long hollow tube that can carry water or other liquids from one place to another.",
        ),
        QAItem(
            question="What does incessant mean?",
            answer="Incessant means something keeps going and going without stopping.",
        ),
        QAItem(
            question="What does whap sound like?",
            answer="Whap is a sharp knocking sound, like something light hitting wood again and again.",
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
        if e.protective:
            bits.append(f"supports={sorted(e.supports)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="lane", problem="whap_tube", fix="wrap", name="Mira", gender="girl", companion="Grandmother", trait="thoughtful"),
    StoryParams(place="lane", problem="whap_tube", fix="tie", name="Rowan", gender="boy", companion="Old Piper", trait="steady"),
    StoryParams(place="lane", problem="rattle_tube", fix="reroute", name="Bram", gender="boy", companion="Uncle Reed", trait="clever"),
]


def explain_rejection(problem: Problem, fix: Optional[Fix]) -> str:
    if fix is None:
        return "(No story: no fitting repair was found for that tubing problem.)"
    return f"(No story: {fix.label} cannot reasonably solve {problem.label}.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "lane"))
    lines.append(asp.fact("affords", "lane", "carry_water"))
    lines.append(asp.fact("affords", "lane", "repair_tube"))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("noise", pid, p.noise))
        lines.append(asp.fact("keyword", pid, p.keyword))
    for fx in FIXES:
        lines.append(asp.fact("fix", fx.id))
        for p in sorted(fx.helps):
            lines.append(asp.fact("helps", fx.id, p))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, F) :- problem(P), fix(F), helps(F, P).
#show valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, f) for _, p, f in valid_combos()}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: tubing, incessant whap, problem solving, and inner monologue."
    )
    ap.add_argument("--place", choices=["lane"])
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=[f.id for f in FIXES])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=Elder_NAMES)
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
    if args.problem and args.fix:
        prob = PROBLEMS[args.problem]
        fx = next(f for f in FIXES if f.id == args.fix)
        if not reasonableness_gate(prob, fx):
            raise StoryError(explain_rejection(prob, fx))

    combos = [c for c in valid_combos()
              if (args.problem is None or c[1] == args.problem)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    _, problem_id, fix_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    companion = args.companion or rng.choice(Elder_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place="lane",
        problem=problem_id,
        fix=fix_id,
        name=name,
        gender=gender,
        companion=companion,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTING, PROBLEMS[params.problem], next(f for f in FIXES if f.id == params.fix),
                 params.name, params.gender, params.companion)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid problem/fix pairs:\n")
        for problem, fix in combos:
            print(f"  {problem:10} {fix}")
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
            header = f"### {p.name}: {p.problem} with {p.fix}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
