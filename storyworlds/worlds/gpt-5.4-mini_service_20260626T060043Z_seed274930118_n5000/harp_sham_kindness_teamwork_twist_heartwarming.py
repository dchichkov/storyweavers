#!/usr/bin/env python3
"""
A small heartwarming storyworld about a harp, a sham offer, and a kinder twist.

Seed premise:
- A child loves a harp and wants to share music with others.
- A sham shortcut or fake fix tempts the world for a moment.
- Kindness and teamwork turn the mistake into a warm, true ending.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "helper"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Venue:
    place: str
    affordance: str
    warm: bool = True


@dataclass
class Problem:
    id: str
    label: str
    mess: str
    risk: str
    tension: str
    keyword: str


@dataclass
class Fix:
    id: str
    label: str
    helps: str
    requires: str
    prep: str
    ending: str


class World:
    def __init__(self, venue: Venue) -> None:
        self.venue = venue
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


@dataclass
class StoryParams:
    venue: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    problem: str
    fix: str
    seed: Optional[int] = None


VENUES = {
    "hall": Venue(place="the community hall", affordance="a small kindness concert"),
    "library": Venue(place="the library room", affordance="a gentle sharing circle"),
    "school": Venue(place="the school stage", affordance="a little music show"),
}

PROBLEMS = {
    "sham_string": Problem(
        id="sham_string",
        label="a sham replacement string",
        mess="crooked sound",
        risk="the harp would sound wrong",
        tension="The shiny string looked quick and easy, but it was a sham.",
        keyword="sham",
    ),
    "sham_tune": Problem(
        id="sham_tune",
        label="a sham tune-up promise",
        mess="stiff music",
        risk="the harp would stay out of tune",
        tension="Someone promised a fast fix, but the promise was a sham.",
        keyword="sham",
    ),
}

FIXES = {
    "tuning": Fix(
        id="tuning",
        label="careful tuning",
        helps="bring the harp back into soft harmony",
        requires="patience",
        prep="sit together and tune it string by string",
        ending="Soon the harp sang true again.",
    ),
    "patching": Fix(
        id="patching",
        label="gentle patching",
        helps="steady the harp's frame",
        requires="two pairs of hands",
        prep="hold the frame steady and mend it with slow care",
        ending="Soon the harp felt steady and ready.",
    ),
}

CHILD_NAMES = ["Maya", "Lina", "Noa", "Tara", "Iris", "Aria", "Sage", "Ruby"]
HELPER_NAMES = ["Grandma", "Mr. Lee", "Auntie June", "Ms. Fern", "Papa", "Nico"]
CHILD_TYPES = ["girl", "boy"]
HELPER_TYPES = ["mother", "father", "helper"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming harp storyworld with kindness, teamwork, and a twist.")
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--child-type", choices=CHILD_TYPES)
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(v, p, f) for v in VENUES for p in PROBLEMS for f in FIXES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    combos = [c for c in combos
              if args.venue is None or c[0] == args.venue
              if True else c]
    combos = [c for c in combos
              if args.problem is None or c[1] == args.problem
              if True else c]
    combos = [c for c in combos
              if args.fix is None or c[2] == args.fix
              if True else c]
    if not combos:
        raise StoryError("No valid story matches those choices.")
    venue, problem, fix = rng.choice(sorted(combos))
    return StoryParams(
        venue=venue,
        child_name=args.name or rng.choice(CHILD_NAMES),
        child_type=args.child_type or rng.choice(CHILD_TYPES),
        helper_name=args.helper or rng.choice(HELPER_NAMES),
        helper_type=args.helper_type or rng.choice(HELPER_TYPES),
        problem=problem,
        fix=fix,
    )


def _say_name(entity: Entity) -> str:
    return entity.id


def story_setup(world: World, child: Entity, helper: Entity, harp: Entity, problem: Problem) -> None:
    world.say(
        f"{child.id} loved the harp and liked the way its strings could make a room feel kind."
    )
    world.say(
        f"At {world.venue.place}, {child.id} was getting ready for {world.venue.affordance} with {helper.id} nearby."
    )
    world.say(
        f"Then a problem appeared: {problem.tension}"
    )


def story_turn(world: World, child: Entity, helper: Entity, harp: Entity, problem: Problem) -> None:
    child.memes["worry"] = 1.0
    child.memes["want"] = 1.0
    world.para()
    world.say(
        f"{child.id} wanted the harp to sound lovely, but the easy answer felt like a {problem.keyword} trick."
    )
    world.say(
        f"{child.id} reached for the quick fix, and for a moment the room went quiet."
    )
    harp.meters["brokenness"] = 1.0
    world.say(
        f"It only made things worse: {problem.risk}."
    )


def story_twist(world: World, child: Entity, helper: Entity, harp: Entity, fix: Fix) -> None:
    world.para()
    helper.memes["kindness"] = 1.0
    child.memes["hope"] = 1.0
    world.say(
        f"{helper.id} smiled and said, \"Let's not use a sham. We'll do this with kindness and teamwork.\""
    )
    world.say(
        f"So they chose {fix.label}: {fix.prep}."
    )
    harp.meters["brokenness"] = 0.0
    harp.meters["tuned"] = 1.0
    world.say(
        f"It needed {fix.requires}, and together they gave it exactly that."
    )
    world.say(fix.ending)
    child.memes["joy"] = 1.0
    helper.memes["warmth"] = 1.0
    world.say(
        f"{child.id} listened, then smiled so wide that even the harp seemed glad."
    )
    world.say(
        f"By the end, {child.id} played for the room, and the music felt like a hug."
    )


def tell(params: StoryParams) -> World:
    venue = VENUES[params.venue]
    problem = PROBLEMS[params.problem]
    fix = FIXES[params.fix]
    world = World(venue)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    harp = world.add(Entity(id="harp", kind="thing", type="harp", label="harp", phrase="a small wooden harp"))
    world.facts.update(child=child, helper=helper, harp=harp, problem=problem, fix=fix, venue=venue)

    story_setup(world, child, helper, harp, problem)
    story_turn(world, child, helper, harp, problem)
    story_twist(world, child, helper, harp, fix)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story about a child named {f["child"].id} and a harp, with a sham mistake and a kinder fix.',
        f"Tell a gentle story at {f['venue'].place} where {f['child'].id} and {f['helper'].id} use teamwork to help a harp sound lovely.",
        f'Write a short story that includes the word "sham" and ends with kindness winning in a small music moment.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    problem = f["problem"]
    fix = f["fix"]
    return [
        QAItem(
            question=f"What did {child.id} want to do with the harp at {world.venue.place}?",
            answer=f"{child.id} wanted to make the harp sound lovely for {world.venue.affordance}.",
        ),
        QAItem(
            question="Why was the quick fix a problem?",
            answer=f"It was a sham, so it did not truly help and left {problem.risk}.",
        ),
        QAItem(
            question=f"How did {helper.id} help in the end?",
            answer=f"{helper.id} chose kindness and teamwork and helped with {fix.label.lower()}.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The harp went from being troubled to sounding warm and true, and the room felt happy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a harp?",
            answer="A harp is a stringed instrument that makes music when its strings are plucked.",
        ),
        QAItem(
            question="What does sham mean?",
            answer="A sham is something that only looks real or helpful but is actually fake.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, caring, and helpful to someone else.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people work together and help each other do a job.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
venue(hall). venue(library). venue(school).
problem(sham_string). problem(sham_tune).
fix(tuning). fix(patching).

valid(V,P,F) :- venue(V), problem(P), fix(F).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for v in VENUES:
        lines.append(asp.fact("venue", v))
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
    for f in FIXES:
        lines.append(asp.fact("fix", f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


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
    StoryParams("hall", "Maya", "girl", "Grandma", "helper", "sham_string", "tuning"),
    StoryParams("library", "Noa", "boy", "Ms. Fern", "helper", "sham_tune", "patching"),
    StoryParams("school", "Aria", "girl", "Papa", "father", "sham_string", "patching"),
]


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
