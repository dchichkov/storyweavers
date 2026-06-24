#!/usr/bin/env python3
"""
A small tall-tale storyworld about a pacifist surprise that becomes a kind,
problem-solving act of uniting a group.

Premise:
- A gentle leader finds a surprising problem.
- Instead of fighting, they gather helpers and solve it kindly.
- The ending proves the group is united.

This file is standalone and follows the Storyweavers storyworld contract.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    feature: str


@dataclass
class Problem:
    id: str
    label: str
    surprise: str
    fix_tool: str
    fix_action: str
    resolved_image: str
    threat: str


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

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


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
PLACES = {
    "ridge": Place("ridge", "the windy ridge", "tall grass"),
    "valley": Place("valley", "the bright valley", "wide paths"),
    "harbor": Place("harbor", "the little harbor", "rope docks"),
}

PROBLEMS = {
    "fallen_gate": Problem(
        id="fallen_gate",
        label="a fallen gate",
        surprise="a gate had toppled across the trail like a sleeping giant",
        fix_tool="rope",
        fix_action="lift the gate together",
        resolved_image="the gate stood straight again, tied with rope and hope",
        threat="the trail was blocked",
    ),
    "lonely_bridge": Problem(
        id="lonely_bridge",
        label="a broken bridge",
        surprise="a bridge had split right down the middle with a splintery crack",
        fix_tool="planks",
        fix_action="patch the bridge plank by plank",
        resolved_image="the bridge stretched across the water once more",
        threat="nobody could cross",
    ),
    "stuck_cart": Problem(
        id="stuck_cart",
        label="a stuck cart",
        surprise="a cart had sunk deep into the mud up to its wooden knees",
        fix_tool="boards",
        fix_action="raise the cart with boards",
        resolved_image="the cart rolled free, as light as a kite",
        threat="the supplies could not move",
    ),
}

TOOLS = {
    "rope": "a coil of rope",
    "planks": "three flat planks",
    "boards": "two strong boards",
}

NAMES = ["Mabel", "Hank", "Ruby", "Otis", "Nell", "Clara", "Jeb", "Pearl"]
TRAITS = ["kind", "calm", "brave", "steady", "gentle"]
SHOUTS = [
    "By my whiskers!",
    "Well butter my biscuit!",
    "Jumping jackdaws!",
]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    problem: str
    hero: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def intro(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    world.say(
        f"{hero.id} was a {hero.memes.get('trait', 'kind')} pacifist who loved to solve trouble "
        f"with a smile and a steady hand."
    )
    world.say(
        f"{helper.id} was the sort of helper who could carry a fence post in one arm and a song in the other."
    )
    world.say(
        f"One day at {world.place.label}, there came a surprise: {problem.surprise}."
    )


def notice_problem(world: World, hero: Entity, problem: Problem) -> None:
    hero.meters["surprise"] = hero.meters.get("surprise", 0) + 1
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"{hero.id} blinked once, twice, and said, \"{random.choice(SHOUTS)}\""
    )
    world.say(
        f"But {hero.id} did not raise a fist or a fuss. {hero.pronoun().capitalize()} took a breath and looked for a kind way through {problem.threat}."
    )


def gather_help(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["unity"] = hero.memes.get("unity", 0) + 1
    helper.memes["kindness"] = helper.memes.get("kindness", 0) + 1
    world.say(
        f"{hero.id} called {helper.id} and a few neighbors to the spot."
    )
    world.say(
        f"\"Let's unite,\" {hero.id} said, \"not to fight the problem, but to fix it.\""
    )


def solve(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    tool = TOOLS[problem.fix_tool]
    hero.meters["problem_solving"] = hero.meters.get("problem_solving", 0) + 1
    helper.meters["problem_solving"] = helper.meters.get("problem_solving", 0) + 1
    world.say(
        f"They found {tool} and put their shoulders to work."
    )
    world.say(
        f"Together they chose to {problem.fix_action}, with {hero.id} steadying one side and {helper.id} steadying the other."
    )
    world.say(
        f"That was kindness with sleeves rolled up, and it was stronger than any grumble."
    )


def resolve(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["unity"] = hero.memes.get("unity", 0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0) + 1
    world.say(
        f"In the end, {problem.resolved_image}."
    )
    world.say(
        f"{hero.id} and {helper.id} stood beside the fix, grinning like two lanterns in the dusk."
    )
    world.say(
        f"Nobody had fought at all, and yet the whole place felt bigger, safer, and more together."
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def tell(place: Place, problem: Problem, hero_name: str, helper_name: str, trait: str) -> World:
    world = World(place=place)
    hero = world.add(Entity(id=hero_name, kind="character", type="pacifist", label="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type="helper", label="helper"))
    hero.memes["trait"] = trait
    helper.memes["trait"] = "helpful"

    world.facts.update(
        hero=hero,
        helper=helper,
        problem=problem,
        place=place,
    )

    intro(world, hero, helper, problem)
    world.para()
    notice_problem(world, hero, problem)
    gather_help(world, hero, helper)
    world.para()
    solve(world, hero, helper, problem)
    resolve(world, hero, helper, problem)

    hero.meters["unite"] = 1
    helper.meters["unite"] = 1
    hero.memes["pacifist"] = 1
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def prompts_for(world: World) -> list[str]:
    f = world.facts
    p: Problem = f["problem"]
    return [
        f'Write a tall tale for little kids about a pacifist who finds "{p.surprise}" and unites everyone to solve it kindly.',
        f"Tell a big-hearted story where {f['hero'].id} uses problem solving instead of fighting at {world.place.label}.",
        f'Write a short story that includes kindness, surprise, and the word "unite" while fixing "{p.label}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    problem: Problem = f["problem"]
    return [
        QAItem(
            question=f"What surprising problem did {hero.id} find at {world.place.label}?",
            answer=f"{hero.id} found {problem.surprise}. That was a surprise that blocked the way and needed calm thinking.",
        ),
        QAItem(
            question=f"How did {hero.id} stay pacifist when the trouble appeared?",
            answer=f"{hero.id} did not fight. {hero.pronoun().capitalize()} took a breath, stayed kind, and looked for a peaceful way to fix the problem.",
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the problem?",
            answer=f"{helper.id} helped {hero.id}, and the two of them united the neighbors around the fix.",
        ),
        QAItem(
            question=f"What was the ending image after they solved it?",
            answer=f"The ending showed {problem.resolved_image}, which proved the problem had been solved kindly.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to be a pacifist?",
            answer="A pacifist is a person who tries not to fight and prefers peaceful ways to solve trouble.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means figuring out what is wrong and using careful steps to fix it.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle and helpful, especially when someone needs care or support.",
        ),
        QAItem(
            question="What does it mean to unite?",
            answer="To unite means to come together as a group and work as one team.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Facts:
% place(P). hero(H). helper(X). problem(Pr). trait(H, T).

% A story is reasonable if a pacifist hero can notice a surprise problem,
% choose kindness, and unite others to solve it.
pacifist_story(P, Pr, H, X) :-
    place(P), problem(Pr), hero(H), helper(X),
    surprise_problem(Pr), kind_hero(H), helpful(X).

can_unite(H, X, Pr) :-
    pacifist(H), kind(H), helpful(X), surprise_problem(Pr).

solves_kindly(H, X, Pr) :-
    can_unite(H, X, Pr),
    problem_solving(H), problem_solving(X),
    kindness(H), kindness(X).

valid_story(P, Pr, H, X) :-
    pacifist_story(P, Pr, H, X),
    can_unite(H, X, Pr),
    solves_kindly(H, X, Pr).
#show valid_story/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for prid in PROBLEMS:
        lines.append(asp.fact("problem", prid))
        lines.append(asp.fact("surprise_problem", prid))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("helper", "helper"))
    lines.append(asp.fact("pacifist", "hero"))
    lines.append(asp.fact("kind", "hero"))
    lines.append(asp.fact("kind_hero", "hero"))
    lines.append(asp.fact("helpful", "helper"))
    lines.append(asp.fact("kindness", "hero"))
    lines.append(asp.fact("kindness", "helper"))
    lines.append(asp.fact("problem_solving", "hero"))
    lines.append(asp.fact("problem_solving", "helper"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid_story")))


def python_valid() -> list[tuple]:
    return sorted((p, pr, "hero", "helper") for p in PLACES for pr in PROBLEMS)


def asp_verify() -> int:
    py = set(python_valid())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP parity matches Python ({len(py)} stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world about a pacifist surprise problem solved with kindness.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(PLACES))
    problem = args.problem or rng.choice(list(PROBLEMS))
    trait = args.trait or rng.choice(TRAITS)
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != hero])
    return StoryParams(place=place, problem=problem, hero=hero, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], PROBLEMS[params.problem], params.hero, params.helper, params.trait)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=prompts_for(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {', '.join(bits) if bits else '(empty)'}")
    return "\n".join(lines)


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
    StoryParams(place="ridge", problem="fallen_gate", hero="Mabel", helper="Hank", trait="kind"),
    StoryParams(place="valley", problem="lonely_bridge", hero="Ruby", helper="Nell", trait="steady"),
    StoryParams(place="harbor", problem="stuck_cart", hero="Otis", helper="Pearl", trait="gentle"),
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
        stories = asp_valid()
        print(f"{len(stories)} compatible stories:")
        for s in stories:
            print(" ", s)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
