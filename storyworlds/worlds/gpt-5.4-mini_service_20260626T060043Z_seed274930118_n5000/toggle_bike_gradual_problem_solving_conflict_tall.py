#!/usr/bin/env python3
"""
A small tall-tale storyworld about a bicycle, a toggle, and gradual problem-solving.

Premise:
- A child loves a big bike.
- A little toggle switch on the bike's bell-light keeps flickering.
- The child wants to ride far, but the bike keeps stopping.

Tension:
- The toggle is loose, so the light cuts out.
- The child and helper disagree about whether to stop now or keep going.

Turn:
- They solve the problem gradually: check, tighten, test, ride, repeat.
- Each small fix changes the bike's state and the child's feelings.

Resolution:
- The bike finally rolls smoothly.
- The light stays on.
- The child rides off under a big, bright sky.

This script follows the Storyweavers contract and supports:
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
"""

from __future__ import annotations

import argparse
import dataclasses
from dataclasses import dataclass, field
import json
import os
import random
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core model
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

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
    name: str
    outdoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    title: str
    cause: str
    symptom: str
    verb: str
    noun: str
    severity: int
    keywords: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    action: str
    tail: str
    helps: set[str] = field(default_factory=set)
    needs: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace_steps: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "hillroad": Place("the hill road", outdoors=True, affords={"ride"}),
    "barnpath": Place("the barn path", outdoors=True, affords={"ride", "repair"}),
    "courtyard": Place("the sunny courtyard", outdoors=True, affords={"ride", "repair"}),
}

PROBLEMS = {
    "toggle_loose": Problem(
        id="toggle_loose",
        title="a loose toggle",
        cause="the little toggle on the bike light was wobbly",
        symptom="the light kept blinking out",
        verb="toggle the light",
        noun="toggle",
        severity=2,
        keywords={"toggle", "light", "blink"},
    ),
    "chain_skip": Problem(
        id="chain_skip",
        title="a skipping chain",
        cause="the bike chain jumped like a frog on a hot stone",
        symptom="the bike lurched and clicked",
        verb="pedal smoothly",
        noun="chain",
        severity=3,
        keywords={"bike", "chain"},
    ),
    "flat_tire": Problem(
        id="flat_tire",
        title="a flat tire",
        cause="one tire sagged down like a tired moon",
        symptom="the bike rolled slow and lopsided",
        verb="roll",
        noun="tire",
        severity=4,
        keywords={"bike", "tire"},
    ),
}

FIXES = {
    "tighten_toggle": Fix(
        id="tighten_toggle",
        label="a tiny wrench and a careful twist",
        action="tighten the toggle",
        tail="took one small turn after another until the switch sat snug",
        helps={"toggle_loose"},
        needs={"toggle"},
    ),
    "oil_chain": Fix(
        id="oil_chain",
        label="a little oil cloth",
        action="oil the chain",
        tail="dropped one drop at a time and wiped the links clean",
        helps={"chain_skip"},
        needs={"bike"},
    ),
    "pump_tire": Fix(
        id="pump_tire",
        label="a hand pump",
        action="pump the tire",
        tail="gave the tire one slow breath after another until it stood proud",
        helps={"flat_tire"},
        needs={"bike"},
    ),
}


GIRL_NAMES = ["Mina", "Tilly", "June", "Ruby", "Nora", "Bess"]
BOY_NAMES = ["Finn", "Owen", "Tate", "Will", "Jude", "Milo"]
HELPERS = ["grandpa", "uncle", "sister", "neighbor"]


@dataclass
class StoryParams:
    place: str
    problem: str
    fix: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
problem_has_fix(P, F) :- problem(P), fix(F), helps(F, P).
valid_story(Pl, P, F, G) :- place(Pl), problem(P), fix(F), problem_has_fix(P, F), protagonist_gender(G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        if PLACES[pid].outdoors:
            lines.append(asp.fact("outdoors", pid))
        for a in sorted(PLACES[pid].affords):
            lines.append(asp.fact("affords", pid, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("problem_keyword", pid, p.noun))
        for k in sorted(p.keywords):
            lines.append(asp.fact("keyword", pid, k))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for h in sorted(f.helps):
            lines.append(asp.fact("helps", fid, h))
    for g in ("girl", "boy"):
        lines.append(asp.fact("protagonist_gender", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_stories())
    import asp
    cl = set(asp.atoms(asp.one_model(asp_program("#show valid_story/4.")), "valid_story"))
    if py == cl:
        print(f"OK: clingo gate matches valid_stories() ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def valid_stories() -> list[tuple[str, str, str, str]]:
    out = []
    for pl in PLACES:
        for prob in PROBLEMS.values():
            for fix in FIXES.values():
                if prob.id in fix.helps:
                    for g in ("girl", "boy"):
                        out.append((pl, prob.id, fix.id, g))
    return out


def reasonableness_gate(place: str, problem: str, fix: str) -> None:
    if problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    if fix not in FIXES:
        raise StoryError("Unknown fix.")
    if problem not in FIXES[fix].helps:
        raise StoryError(f"(No story: {FIXES[fix].action} does not honestly solve {PROBLEMS[problem].title}.)")
    if "bike" not in FIXES[fix].needs and problem == "toggle_loose":
        pass


def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"hope": 1.0, "ride": 0.0},
        memes={"worry": 0.0, "pride": 0.0, "conflict": 0.0, "relief": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper,
        label=params.helper,
        meters={"patience": 1.0},
        memes={"calm": 1.0},
    ))
    bike = world.add(Entity(
        id="bike",
        kind="thing",
        type="bike",
        label="bike",
        phrase="a long-legged bicycle with a bright lamp",
        owner=hero.id,
        meters={"balance": 1.0, "speed": 0.0, "light": 0.0},
        memes={"stuck": 0.0, "trust": 0.0},
        attrs={"wheel": "big", "style": "tall"},
    ))
    problem = PROBLEMS[params.problem]
    fix = FIXES[params.fix]
    world.facts.update(hero=hero, helper=helper, bike=bike, problem=problem, fix=fix)
    return world


def propagate(world: World) -> None:
    # deterministic simple causal loops
    bike = world.get("bike")
    problem: Problem = world.facts["problem"]  # type: ignore[assignment]
    if problem.id == "toggle_loose" and bike.meters["light"] < THRESHOLD:
        sig = ("light_flicker",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.trace_steps.append("light flickered out")
            bike.memes["stuck"] += 1.0
    if problem.id == "chain_skip" and bike.meters["speed"] < THRESHOLD:
        sig = ("chain_skip",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.trace_steps.append("chain skipped")
            bike.memes["stuck"] += 1.0
    if problem.id == "flat_tire" and bike.meters["balance"] < THRESHOLD:
        sig = ("flat_tire",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.trace_steps.append("tire sagged")
            bike.memes["stuck"] += 1.0


def introduce(world: World) -> None:
    hero = world.facts["hero"]  # type: ignore[assignment]
    problem: Problem = world.facts["problem"]  # type: ignore[assignment]
    world.say(f"{hero.id} was a tall little rider who loved the bike more than a kite loves the wind.")
    world.say(f"That bike had {problem.cause}, and everybody could see it from a mile away.")


def conflict(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    problem: Problem = world.facts["problem"]  # type: ignore[assignment]
    bike: Entity = world.facts["bike"]  # type: ignore[assignment]

    hero.memes["worry"] += 1.0
    helper.memes["calm"] += 0.5
    world.say(f"One day, {hero.id} tried to ride off, but {problem.symptom}.")
    world.say(f"{helper.label.capitalize()} raised a hand and said, 'Not so fast, kiddo. Let's solve this gradual and proper.'")
    hero.memes["conflict"] += 1.0
    bike.memes["stuck"] += 1.0
    propagate(world)


def gradual_fix(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    bike: Entity = world.facts["bike"]  # type: ignore[assignment]
    problem: Problem = world.facts["problem"]  # type: ignore[assignment]
    fix: Fix = world.facts["fix"]  # type: ignore[assignment]

    world.para()
    world.say(f"{hero.id} and {helper.label} did not hurry the thing. They looked, listened, and took one little step at a time.")
    if problem.id == "toggle_loose":
        bike.meters["light"] += 1.0
        world.say(f"First they found the loose toggle. Then they used {fix.label} and {fix.tail}.")
        bike.meters["light"] += 1.0
    elif problem.id == "chain_skip":
        bike.meters["speed"] += 1.0
        world.say(f"First they found the skipping chain. Then they used {fix.label} and {fix.tail}.")
        bike.meters["speed"] += 1.0
    else:
        bike.meters["balance"] += 1.0
        world.say(f"First they found the sagging tire. Then they used {fix.label} and {fix.tail}.")
        bike.meters["balance"] += 1.0
    hero.memes["conflict"] = 0.0
    hero.memes["relief"] += 1.0
    helper.meters["patience"] += 1.0
    bike.memes["trust"] += 1.0
    world.say(f"The bike answered with a happy shine, as if it knew the answer all along.")
    world.say(f"After that, {hero.id} could ride again, and the road looked wide as a river.")


def ending(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    bike: Entity = world.facts["bike"]  # type: ignore[assignment]
    world.para()
    world.say(f"In the end, the bike rolled smooth and tall, and the little toggle stayed put like a star nailed to the sky.")
    world.say(f"{hero.id} laughed so hard the road seemed to grin back, and {helper.label} waved until the rider was a speck of joy in the distance.")
    bike.meters["speed"] += 1.0
    hero.meters["ride"] += 1.0
    hero.memes["pride"] += 1.0


def tell(params: StoryParams) -> World:
    world = build_world(params)
    introduce(world)
    conflict(world)
    gradual_fix(world)
    ending(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    problem: Problem = f["problem"]  # type: ignore[assignment]
    fix: Fix = f["fix"]  # type: ignore[assignment]
    return [
        f"Write a tall-tale story about {hero.id}, a bike, and a {problem.noun} problem that gets solved gradually.",
        f"Tell a gentle conflict-and-problem-solving story where a child and helper fix the {problem.title} with {fix.label}.",
        f"Write a kid-friendly story using the words toggle, bike, and gradual, and end with the bike rolling smoothly again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    problem: Problem = f["problem"]  # type: ignore[assignment]
    fix: Fix = f["fix"]  # type: ignore[assignment]
    bike: Entity = f["bike"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What was wrong with the bike in the story?",
            answer=f"The bike had {problem.cause}, so {problem.symptom}.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.label} solve the problem?",
            answer=f"They solved it gradual and careful, using {fix.label} to {fix.action}.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"The bike rolled smoothly again, and the little toggle stayed steady instead of blinking out.",
        ),
        QAItem(
            question=f"How did {hero.id} feel after the fix?",
            answer=f"{hero.id} felt relief and pride because the ride could finally go on.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a toggle?",
            answer="A toggle is a small switch you flip one way or the other to turn something on, off, or change its setting.",
        ),
        QAItem(
            question="What is a bike for?",
            answer="A bike is for riding. It lets someone roll along by pedaling and balancing on two wheels.",
        ),
        QAItem(
            question="What does gradual mean?",
            answer="Gradual means happening in small steps instead of all at once.",
        ),
        QAItem(
            question="Why is patient problem solving helpful?",
            answer="Patient problem solving helps because small careful steps can find what is wrong and fix it without making a bigger mess.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    if world.trace_steps:
        lines.append("steps: " + ", ".join(world.trace_steps))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Contract functions
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld: toggle, bike, gradual problem solving.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--problem", choices=PROBLEMS.keys())
    ap.add_argument("--fix", choices=FIXES.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.problem and args.fix and args.problem not in FIXES[args.fix].helps:
        raise StoryError(f"(No story: {FIXES[args.fix].action} does not honestly solve {PROBLEMS[args.problem].title}.)")
    combos = valid_stories()
    combos = [c for c in combos if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.fix is None or c[2] == args.fix)
              and (args.gender is None or c[3] == args.gender)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, fix, gender = rng.choice(sorted(combos))
    name = args.name or choose_name(gender, rng)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, problem=problem, fix=fix, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
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
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="hillroad", problem="toggle_loose", fix="tighten_toggle", name="Mina", gender="girl", helper="grandpa"),
    StoryParams(place="barnpath", problem="chain_skip", fix="oil_chain", name="Finn", gender="boy", helper="uncle"),
    StoryParams(place="courtyard", problem="flat_tire", fix="pump_tire", name="Ruby", gender="girl", helper="sister"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for row in stories:
            print("  ", row)
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
            except StoryError as e:
                print(e)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
