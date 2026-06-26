#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/ban_bureaucratic_happy_ending_bad_ending_teamwork.py
=============================================================================================================

A small heartwarming storyworld about a bureaucratic ban, a worried child,
and the teamwork that can either lift the problem into a happy ending or leave
it as a bad ending.

Seed tale:
---
A city clerk puts a bureaucratic ban on the community fountain after a leak.
A child named Pip loves watering the garden there, but now the plants are thirsty.
Pip and a neighbor try to fix the problem by working together: they fetch small
buckets, fill out forms, and ask the clerk to check the repair.
If they cooperate and the paperwork clears, the ban is lifted and the garden
blooms. If they fail, the flowers stay droopy and the gate stays closed.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
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


@dataclass
class Place:
    name: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    prep: str
    tail: str
    solves: set[str]
    requires: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    problem: str
    ending: str
    name: str
    helper: str
    clerk: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
        self.history: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.history.append(text)

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
        w.zone = set(self.zone)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


def _r_wilt(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.kind != "plant":
            continue
        if ent.meters.get("dry", 0) < THRESHOLD:
            continue
        sig = ("wilt", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["sad"] = ent.meters.get("sad", 0) + 1
        out.append(f"The {ent.label} drooped a little more.")
    return out


def _r_lift_ban(world: World) -> list[str]:
    out: list[str] = []
    clerk = world.entities.get("clerk")
    board = world.entities.get("board")
    if not clerk or not board:
        return out
    if board.memes.get("paperwork_done", 0) < THRESHOLD:
        return out
    sig = ("lift",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    board.meters["banned"] = 0
    clerk.memes["pride"] = clerk.memes.get("pride", 0) + 1
    out.append("The clerk stamped the last page and lifted the ban.")
    return out


CAUSAL_RULES = [
    _r_wilt,
    _r_lift_ban,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def predict_outcome(world: World, hero: Entity, problem: Problem, remedy: Remedy) -> dict:
    sim = world.copy()
    _do_problem(sim, hero.id, problem, narrate=False)
    _teamwork(sim, hero.id, remedy, narrate=False)
    board = sim.get("board")
    plants = sim.get("flowers")
    return {
        "ban_lifted": board.meters.get("banned", 0) < THRESHOLD,
        "plants_ok": plants.meters.get("sad", 0) < THRESHOLD,
    }


def _do_problem(world: World, hero_id: str, problem: Problem, narrate: bool = True) -> None:
    hero = world.get(hero_id)
    world.zone = set(problem.zone)
    hero.meters[problem.id] = hero.meters.get(problem.id, 0) + 1
    if narrate:
        world.say(f"{hero.id} wanted to {problem.verb}, even though the sign said no.")
    if problem.id == "water":
        flowers = world.get("flowers")
        flowers.meters["dry"] = flowers.meters.get("dry", 0) + 1
        if narrate:
            world.say(f"The flowers got thirsty while the ban stayed up.")
    propagate(world, narrate=narrate)


def _teamwork(world: World, hero_id: str, remedy: Remedy, narrate: bool = True) -> None:
    board = world.get("board")
    helper = world.get("helper")
    hero = world.get(hero_id)
    if helper.memes.get("helpful", 0) < THRESHOLD:
        return
    board.memes["paperwork_done"] = board.memes.get("paperwork_done", 0) + 1
    helper.memes["teamwork"] = helper.memes.get("teamwork", 0) + 1
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    if narrate:
        world.say(
            f"{hero.id} and {helper.label} worked together: they did the paperwork, "
            f"followed the rules, and brought the forms back."
        )
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity, helper: Entity, clerk: Entity, problem: Problem) -> None:
    world.say(
        f"{hero.id} was a little {next((t for t in hero.traits if t != 'little'), 'kind')} "
        f"{hero.type} who liked to help at {world.place.name}."
    )
    world.say(
        f"{hero.id} loved {problem.gerund}, because it made the garden feel bright and alive."
    )
    world.say(
        f"But {clerk.label} had put up a bureaucratic ban, and the sign made everything feel stuck."
    )
    world.say(
        f"Luckily, {helper.label} was nearby and ready to work as a teammate."
    )


def conflict(world: World, hero: Entity, clerk: Entity, problem: Problem) -> None:
    world.para()
    world.say(
        f"{hero.id} wanted to {problem.verb}, but the ban said to stop."
    )
    world.say(
        f"{hero.pronoun().capitalize()} looked at the thirsty garden and felt torn between kindness and rules."
    )
    world.say(
        f"{clerk.label} pointed to the sign and said the city needed proper papers first."
    )


def resolution_happy(world: World, hero: Entity, helper: Entity, clerk: Entity, problem: Problem, remedy: Remedy) -> None:
    world.para()
    world.say(
        f"{hero.id} took a breath, and {helper.label} smiled. They chose teamwork instead of arguing."
    )
    world.say(
        f"They filled the forms, checked the leak, and carried small buckets where they were allowed."
    )
    _teamwork(world, hero.id, remedy, narrate=True)
    board = world.get("board")
    if board.meters.get("banned", 0) < THRESHOLD:
        world.say(
            f"With a final stamp, {clerk.label} lifted the ban."
        )
    flowers = world.get("flowers")
    flowers.meters["bloom"] = flowers.meters.get("bloom", 0) + 1
    world.say(
        f"The flowers perked up, and {hero.id} smiled because the garden was safe again."
    )
    world.say(
        f"That evening, {hero.id}, {helper.label}, and {clerk.label} stood together under the soft light, proud of their gentle teamwork."
    )


def resolution_bad(world: World, hero: Entity, helper: Entity, clerk: Entity, problem: Problem, remedy: Remedy) -> None:
    world.para()
    world.say(
        f"{hero.id} tried to fix everything fast, but the papers stayed in a messy pile."
    )
    world.say(
        f"Without teamwork, the ban stayed on the gate."
    )
    world.say(
        f"The flowers drooped, and {hero.id} had to go home with a heavy, quiet heart."
    )


VALID_COMBOS = [
    ("garden", "water", "happy"),
    ("garden", "water", "bad"),
    ("library", "borrow", "happy"),
    ("library", "borrow", "bad"),
]


SETTINGS = {
    "garden": Place(name="the community garden", indoors=False, affords={"water"}),
    "library": Place(name="the little library", indoors=True, affords={"borrow"}),
}

PROBLEMS = {
    "water": Problem(
        id="water",
        verb="water the plants",
        gerund="watering the plants",
        rush="run to the fountain",
        risk="thirst",
        zone={"ground"},
        keyword="ban",
        tags={"ban", "bureaucratic", "garden"},
    ),
    "borrow": Problem(
        id="borrow",
        verb="borrow a storybook",
        gerund="reading storybooks",
        rush="run to the shelf",
        risk="waiting",
        zone={"hand"},
        keyword="bureaucratic",
        tags={"ban", "bureaucratic", "library"},
    ),
}

REMEDIES = {
    "water": Remedy(
        id="paperwork",
        label="the paperwork plan",
        prep="fill out the forms",
        tail="walked the pages to the clerk",
        solves={"water"},
    ),
    "borrow": Remedy(
        id="checkout",
        label="the checkout plan",
        prep="use the borrowing card",
        tail="brought the card to the desk",
        solves={"borrow"},
    ),
}

NAMES = ["Pip", "Mila", "Noah", "Luna", "Toby", "Ivy", "June", "Eli"]
HELPERS = ["Nora", "Ben", "Sage", "Ada", "Theo", "Mara"]
CLERKS = ["Ms. Reed", "Mr. Bell", "Mrs. Hale", "Ms. Finch"]
TRAITS = ["kind", "patient", "cheerful", "brave", "gentle", "curious"]


def valid_combos() -> list[tuple[str, str, str]]:
    return list(VALID_COMBOS)


@dataclass
class StoryWorld:
    world: World
    hero: Entity
    helper: Entity
    clerk: Entity
    board: Entity
    flowers: Entity
    problem: Problem
    remedy: Remedy
    ending: str


def build_world(params: StoryParams) -> StoryWorld:
    place = SETTINGS[params.place]
    problem = PROBLEMS[params.problem]
    remedy = REMEDIES[params.problem]
    world = World(place)
    hero = world.add(Entity(id=params.name, kind="character", type="boy" if params.name in {"Noah", "Toby", "Eli"} else "girl", traits=["little", params.trait]))
    helper = world.add(Entity(id="helper", kind="character", type="friend", label=params.helper, memes={"helpful": 1}))
    clerk = world.add(Entity(id="clerk", kind="character", type="adult", label=params.clerk, memes={"strict": 1}))
    board = world.add(Entity(id="board", type="noticeboard", label="the noticeboard", meters={"banned": 1}, memes={"paperwork_done": 0}))
    flowers = world.add(Entity(id="flowers", kind="plant", type="flowers", label="flowers", meters={"dry": 0}))
    world.facts.update(hero=hero, helper=helper, clerk=clerk, board=board, flowers=flowers, problem=problem, remedy=remedy)
    return StoryWorld(world, hero, helper, clerk, board, flowers, problem, remedy, params.ending)


def tell(sw: StoryWorld) -> World:
    w = sw.world
    intro(w, sw.hero, sw.helper, sw.clerk, sw.problem)
    conflict(w, sw.hero, sw.clerk, sw.problem)
    if sw.ending == "happy":
        resolution_happy(w, sw.hero, sw.helper, sw.clerk, sw.problem, sw.remedy)
    else:
        resolution_bad(w, sw.hero, sw.helper, sw.clerk, sw.problem, sw.remedy)
    if sw.ending == "happy":
        sw.hero.memes["joy"] = sw.hero.memes.get("joy", 0) + 1
        sw.hero.memes["hope"] = sw.hero.memes.get("hope", 0) + 1
    else:
        sw.hero.memes["sad"] = sw.hero.memes.get("sad", 0) + 1
    return w


KNOWLEDGE = {
    "ban": [
        ("What is a ban?", "A ban is a rule that says something is not allowed for a while."),
    ],
    "bureaucratic": [
        ("What does bureaucratic mean?", "Bureaucratic means something is handled by official rules, papers, and offices."),
    ],
    "teamwork": [
        ("What is teamwork?", "Teamwork is when people help each other and do a job together."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story for a young child about a bureaucratic ban and teamwork in {world.place.name}.',
        f"Tell a short story where {f['hero'].id} wants to {f['problem'].verb}, but {f['clerk'].label} has made a ban, and then teamwork helps.",
        f'Write a gentle story that uses the word "{f["problem"].keyword}" and ends with either a happy ending or a bad ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, clerk, problem = f["hero"], f["helper"], f["clerk"], f["problem"]
    ending = "happy ending" if world.get("board").meters.get("banned", 0) < THRESHOLD else "bad ending"
    qa = [
        QAItem(
            question=f"Who was the story about at {world.place.name}?",
            answer=f"It was about {hero.id}, a little {hero.pronoun('possessive')} {hero.type}, who wanted to help the garden."
        ),
        QAItem(
            question=f"What did {hero.id} want to do even though there was a ban?",
            answer=f"{hero.id} wanted to {problem.verb}, but the sign said no until the papers were checked."
        ),
        QAItem(
            question=f"Who helped {hero.id} with the problem?",
            answer=f"{helper.label} helped by doing teamwork and helping with the official papers."
        ),
        QAItem(
            question=f"Was this a happy ending or a bad ending?",
            answer=f"It was a {ending}."
        ),
    ]
    return qa


def world_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in ["ban", "bureaucratic", "teamwork"]:
        qas = KNOWLEDGE[tag]
        out.extend(QAItem(question=q, answer=a) for q, a in qas)
    return out


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
    lines.append("== (3) World knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for (n, *_) in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for r in sorted(p.zone):
            lines.append(asp.fact("zone", pid, r))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        for s in sorted(r.solves):
            lines.append(asp.fact("solves", rid, s))
    lines.append(asp.fact("ending", "happy"))
    lines.append(asp.fact("ending", "bad"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Problem, Ending) :- affords(Place, Problem), ending(Ending).
compatible(Place, Problem, happy) :- valid(Place, Problem, happy).
compatible(Place, Problem, bad) :- valid(Place, Problem, bad).
#show compatible/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming storyworld with a bureaucratic ban and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--ending", choices=["happy", "bad"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--clerk")
    ap.add_argument("--trait")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.ending is None or c[2] == args.ending)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, ending = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        problem=problem,
        ending=ending,
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        clerk=args.clerk or rng.choice(CLERKS),
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    sw = build_world(params)
    world = tell(sw)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="garden", problem="water", ending="happy", name="Pip", helper="Nora", clerk="Ms. Reed", trait="kind"),
    StoryParams(place="garden", problem="water", ending="bad", name="Mila", helper="Ben", clerk="Mrs. Hale", trait="patient"),
    StoryParams(place="library", problem="borrow", ending="happy", name="Noah", helper="Ada", clerk="Mr. Bell", trait="curious"),
    StoryParams(place="library", problem="borrow", ending="bad", name="Luna", helper="Mara", clerk="Ms. Finch", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for combo in combos:
            print(" ", combo)
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
            header = f"### {p.name}: {p.problem} at {p.place} ({p.ending})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
