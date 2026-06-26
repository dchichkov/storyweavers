#!/usr/bin/env python3
"""
A nursery-rhyme storyworld about an orphan, a ruckus, and a waitress.

The small simulated domain:
- A lonely orphan in a cozy diner
- A noisy ruckus that upsets the room
- A waitress who helps solve the problem
- A transformation from upset to calm
- A moral value: kindness, honesty, and helping

The world is intentionally compact and constraint-checked. A valid story needs:
- one child who is an orphan
- one upsetting ruckus in the diner
- one waitress who can help
- a problem-solving turn that changes the state
- an ending that proves the transformation

The prose aims for a nursery-rhyme feel: short, gentle, concrete, and rhythmic.
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
# World constants
# ---------------------------------------------------------------------------

MOODS = ("sad", "worried", "hopeful", "calm", "kind")
VALUES = ("kindness", "honesty", "helpfulness")
PLACES = ("little diner", "corner diner", "sunny diner", "tinny diner")
PROBLEM_TAGS = ("spill", "lost coin", "broken tray", "scattered spoon")
FIXES = ("sweep the floor", "pick up the spoons", "share the coins", "tell the truth")
NAMES = ("Mina", "Toby", "Pip", "Lena", "Ned", "Ruby", "Milo", "June")
WAITRESS_NAMES = ("Mabel", "Nora", "Elsie", "Hazel", "Dot", "Ivy")


# ---------------------------------------------------------------------------
# Entity model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def mood(self) -> str:
        vals = [(k, v) for k, v in self.memes.items() if v > 0]
        if not vals:
            return "calm"
        vals.sort(key=lambda kv: kv[1], reverse=True)
        return vals[0][0]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    orphan_name: str
    waitress_name: str
    problem: str
    fix: str
    value: str
    seed: Optional[int] = None


@dataclass
class Setting:
    place: str
    warm: bool = True


SETTINGS = {p.replace(" ", "_"): Setting(place=p) for p in PLACES}


@dataclass
class Problem:
    id: str
    verb: str
    noun: str
    mess: str
    stress: str
    needs: str
    tag: str


PROBLEMS = {
    "spill": Problem(
        id="spill",
        verb="spill the milk",
        noun="milk",
        mess="a white puddle",
        stress="the room got messy",
        needs="a mop",
        tag="spill",
    ),
    "lost_coin": Problem(
        id="lost_coin",
        verb="search for a lost coin",
        noun="coin",
        mess="a worried search",
        stress="the child could not pay",
        needs="a kind helper",
        tag="coin",
    ),
    "broken_tray": Problem(
        id="broken_tray",
        verb="fix the broken tray",
        noun="tray",
        mess="a wobbling tray",
        stress="the cups were in danger",
        needs="steady hands",
        tag="tray",
    ),
    "scattered_spoon": Problem(
        id="scattered_spoon",
        verb="gather the spoons",
        noun="spoons",
        mess="shiny spoons everywhere",
        stress="the floor was all in a flutter",
        needs="a tidy plan",
        tag="spoon",
    ),
}


@dataclass
class Fix:
    id: str
    action: str
    result: str
    value: str


FIXES_REGISTRY = {
    "sweep": Fix("sweep", "sweep the floor", "the diner looked neat again", "helpfulness"),
    "spoons": Fix("spoons", "pick up the spoons", "the silver spoons were back in their bowl", "kindness"),
    "coins": Fix("coins", "share the coins", "the child could pay with a smile", "honesty"),
    "truth": Fix("truth", "tell the truth", "the air felt lighter and honest", "honesty"),
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when an orphan, a waitress, and a problem all fit together.
valid_story(P, Prob, Fix) :-
    place(P),
    problem(Prob),
    fix(Fix),
    helps(Fix, Prob).

% The problem is solvable when the fix matches the problem type.
helps(sweep, spill).
helps(spoons, scattered_spoon).
helps(coins, lost_coin).
helps(truth, lost_coin).

% The moral value is attached to the fix.
moral(sweep, helpfulness).
moral(spoons, kindness).
moral(coins, honesty).
moral(truth, honesty).

% A story must include the seed words in the domain model.
seed_word(orphan).
seed_word(ruckus).
seed_word(waitress).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for key, setting in SETTINGS.items():
        lines.append(asp.fact("place", key))
        lines.append(asp.fact("setting_place", key, setting.place))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for fid in FIXES_REGISTRY:
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("moral", fid, FIXES_REGISTRY[fid].value))
    lines.append(asp.fact("seed_word", "orphan"))
    lines.append(asp.fact("seed_word", "ruckus"))
    lines.append(asp.fact("seed_word", "waitress"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = set(valid_combos())
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    got = set(asp.atoms(model, "valid_story"))
    if expected == got:
        print(f"OK: ASP parity holds for {len(expected)} valid stories.")
        return 0
    print("MISMATCH between Python and ASP:")
    print("python-only:", sorted(expected - got))
    print("asp-only:", sorted(got - expected))
    return 1


# ---------------------------------------------------------------------------
# Python reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for p in SETTINGS:
        for prob in PROBLEMS:
            for fix in FIXES_REGISTRY:
                if is_reasonable(prob, fix):
                    combos.append((p, prob, fix))
    return combos


def is_reasonable(problem_id: str, fix_id: str) -> bool:
    return (
        (problem_id == "spill" and fix_id == "sweep")
        or (problem_id == "lost_coin" and fix_id in {"coins", "truth"})
        or (problem_id == "broken_tray" and fix_id == "truth")
        or (problem_id == "scattered_spoon" and fix_id == "spoons")
    )


def explain_rejection(problem_id: str, fix_id: str) -> str:
    prob = PROBLEMS[problem_id]
    fix = FIXES_REGISTRY[fix_id]
    return (
        f"(No story: {fix.action} does not honestly solve {prob.verb}. "
        f"Try a fix that matches the problem.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: orphan, ruckus, waitress.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
    ap.add_argument("--fix", choices=sorted(FIXES_REGISTRY))
    ap.add_argument("--name")
    ap.add_argument("--waitress")
    ap.add_argument("--value", choices=sorted(VALUES))
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
    if args.problem and args.fix and not is_reasonable(args.problem, args.fix):
        raise StoryError(explain_rejection(args.problem, args.fix))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, prob, fix = rng.choice(sorted(combos))
    return StoryParams(
        place=SETTINGS[place].place,
        orphan_name=args.name or rng.choice(NAMES),
        waitress_name=args.waitress or rng.choice(WAITRESS_NAMES),
        problem=prob,
        fix=fix,
        value=args.value or FIXES_REGISTRY[fix].value,
    )


def make_world(params: StoryParams) -> World:
    world = World(place=params.place)
    orphan = world.add(Entity(id="orphan", kind="character", label=params.orphan_name, type="orphan"))
    waitress = world.add(Entity(id="waitress", kind="character", label=params.waitress_name, type="waitress"))
    prob = PROBLEMS[params.problem]
    fix = FIXES_REGISTRY[params.fix]

    orphan.memes["sad"] = 2.0
    orphan.memes["worried"] = 1.0
    waitress.memes["kind"] = 1.0

    world.facts.update(orphan=orphan, waitress=waitress, problem=prob, fix=fix)
    return world


def tell_story(world: World, params: StoryParams) -> None:
    orphan = world.get("orphan")
    waitress = world.get("waitress")
    prob = PROBLEMS[params.problem]
    fix = FIXES_REGISTRY[params.fix]

    world.say(f"In a {world.place}, a little orphan named {orphan.label} sat still as a mouse.")
    world.say(f"A ruckus rose up—clatter, chatter, and a tumble—while {orphan.label} looked on with wide eyes.")
    world.say(f"The kind waitress {waitress.label} came along and saw the trouble right away.")
    world.say(f"{orphan.label} wanted to {prob.verb}, but {prob.stress}.")
    world.say(f"So {waitress.label} said, 'Come now, small dear, let's {fix.action}.'")
    world.say(f"Together they did it, and {fix.result}.")
    orphan.memes["hopeful"] = 2.0
    orphan.memes["calm"] = 2.0
    orphan.memes["kind"] = 1.0
    waitress.memes["hopeful"] = 1.0
    world.facts["resolved"] = True
    world.facts["moral"] = fix.value
    world.facts["ending"] = f"{orphan.label} smiled, and the diner was gentle again."


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    prob = f["problem"]
    fix = f["fix"]
    orphan = f["orphan"].label
    waitress = f["waitress"].label
    return [
        f"Write a short nursery-rhyme story about an orphan, a ruckus, and a waitress in a {world.place}.",
        f"Tell how {orphan} meets a ruckus in a {world.place} and {waitress} helps solve the problem.",
        f"Write a gentle story that ends with the moral value of {fix.value} after the trouble is fixed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    orphan = f["orphan"].label
    waitress = f["waitress"].label
    prob = f["problem"]
    fix = f["fix"]
    return [
        QAItem(
            question="Who was the orphan in the story?",
            answer=f"The orphan was {orphan}.",
        ),
        QAItem(
            question="Who helped solve the ruckus?",
            answer=f"The waitress {waitress} helped solve the ruckus by {fix.action}.",
        ),
        QAItem(
            question="What problem caused the trouble?",
            answer=f"The trouble was that the child had to {prob.verb}.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"The upset turned into calm, and the diner ended neat and kind.",
        ),
        QAItem(
            question="What moral value did the story show?",
            answer=f"The story showed {fix.value}, because helping made everything better.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an orphan?",
            answer="An orphan is a child who does not have living parents to care for them.",
        ),
        QAItem(
            question="What is a ruckus?",
            answer="A ruckus is a noisy, messy disturbance that makes a place feel upset and busy.",
        ),
        QAItem(
            question="What does a waitress do?",
            answer="A waitress serves food and drinks, and she often helps keep a restaurant calm and tidy.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, caring, and helpful to other people.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        lines.append(
            f"  {ent.id}: kind={ent.kind} label={ent.label!r} "
            f"meters={ent.meters} memes={ent.memes}"
        )
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


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


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell_story(world, params)
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
    StoryParams(place="little diner", orphan_name="Mina", waitress_name="Mabel", problem="spill", fix="sweep", value="helpfulness"),
    StoryParams(place="corner diner", orphan_name="Toby", waitress_name="Hazel", problem="lost_coin", fix="truth", value="honesty"),
    StoryParams(place="sunny diner", orphan_name="Pip", waitress_name="Ivy", problem="scattered_spoon", fix="spoons", value="kindness"),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify_gate() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    return 1


def asp_program_full(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program_full("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify_gate())
    if args.asp:
        stories = asp_valid_combos()
        print(f"{len(stories)} compatible story combos:")
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
